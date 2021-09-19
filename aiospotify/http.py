from typing import Any, Dict, List, Optional, Union
import aiohttp
import asyncio
import urllib.parse
import base64
import datetime
import json
from aiohttp import web

from .errors import Forbidden, HTTPException, NotFound, Unauthorized, BadRequest
    
class Authentication:
    URL = 'https://accounts.spotify.com/api/token'
    def __init__(self, client_id: Union[str, int], client_secret: str, session: aiohttp.ClientSession) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session

        self.expires_at: Optional[datetime.datetime] = None
        self._refresh_token = None
        self.token = None

    def build_oauth_url(self, scopes: List[str]=None):
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://127.0.0.1:8080/callback',
        }

        if scopes:
            params['scope'] = ' '.join(scopes)

        return '{}?{}'.format('https://accounts.spotify.com/authorize', urllib.parse.urlencode(params))

    def build_basic_token(self):
        client_id = urllib.parse.quote(str(self.client_id))
        client_secret = urllib.parse.quote(self.client_secret)

        token = base64.b64encode('{}:{}'.format(client_id, client_secret).encode('utf8'))
        token = token.decode('utf-8')

        return token

    async def get_token(self):
        if self.is_expired():
            if self.is_oauth2():
                await self.refresh_token()
            else:
                await self.fetch_token()

        if self.token:
            return self.token

        return await self.fetch_token()

    async def fetch_token(self) -> str:
        data = {
            'grant_type': 'client_credentials'
        }

        token = self.build_basic_token()
        headers = {
            'Authorization': 'Basic ' + token,
        }

        async with self.session.request('POST', self.URL, headers=headers, data=data) as response:
            data = await response.json()
            self.update(data)

        return self.token

    def is_expired(self):
        if not self.expires_at:
            return False

        return datetime.datetime.utcnow() > self.expires_at

    def is_oauth2(self):
        return self._refresh_token is not None

    async def refresh_token(self):
        data = {
            'refresh_token': self.token,
            'grant_type': 'refresh_token'
        }

        async with self.session.request('POST', self.URL, data=data) as response:
            data = await response.json()
            self.update(data)
        
        return self.token

    def update(self, data: Dict[str, Any]):
        self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=data['expires_in'])
        self.token = data['access_token']
        self._refresh_token = data.get('refresh_token')

class OAuth2Server:
    def __init__(self, loop: asyncio.AbstractEventLoop, auth: Authentication) -> None:
        self.loop = loop
        self.auth = auth
        self.app = web.Application()
        self.reveiced = asyncio.Event()
        self.app.router.add_get('/callback', self.handle_auth)

        self.code = None

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner)
        await self.site.start()  

    async def close(self):
        await self.site.stop()
        await self.runner.cleanup()

    async def wait(self):
        await self.start()

        await self.reveiced.wait()
        await self.close()

        token = self.auth.build_basic_token()
        headers = {
            'Authorization': 'Basic ' + token,
        }

        payload = {
            'grant_type': 'authorization_code',
            'code': self.code,
            'redirect_uri': 'http://127.0.0.1:8080/callback'
        }

        async with self.auth.session.request('POST', self.auth.URL, headers=headers, data=payload) as response:
            data = await response.json()
            self.auth.update(data)

        return self.auth.token

    async def handle_auth(self, request: web.Request) -> web.Response:
        self.reveiced.set()

        query = request.query
        self.code = query['code']

        return web.Response(text='OK')

class HTTPClient:
    URL = 'https://api.spotify.com/v1'
    def __init__(
        self, 
        client_id: Union[str, int], 
        client_secret: str, 
        *, 
        loop: asyncio.AbstractEventLoop=None, 
        session: aiohttp.ClientSession=None,
        oauth2: bool=True
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(loop=self.loop)
        self.locks: Dict[str, asyncio.Lock] = {}

        self.auth = Authentication(client_id, client_secret, self.session)
        self.errors = {
            401: Unauthorized,
            403: Forbidden,
            404: NotFound,
            400: BadRequest
        }

        if oauth2:
            self.server = OAuth2Server(self.loop, self.auth)
            self.loop.create_task(self.server.wait())

    async def read(self, url: str):
        async with self.session.get(url) as response:
            return await response.read()

    async def request(self, path: str, method: str, **kwargs) -> Dict[str, Any]:
        token = await self.auth.get_token()
        bucket = f'{path}-{method}'

        lock = self.locks.get(bucket)
        if lock is None:
            self.locks[bucket] = lock = asyncio.Lock()

        if not kwargs.pop('is_full_url', False):
            url = self.URL + path
        else:
            url = path

        headers = {
            'Authorization': 'Bearer ' + token
        }

        async with lock:
            for retry in range(3):

                async with self.session.request(method, url, headers=headers, **kwargs) as response:
                    data = await response.json(encoding='utf-8')

                    if 300 > response.status >= 200:
                        return data

                    if response.status == 429:
                        retry_after = int(response.headers['Retry-After'])
                        await asyncio.sleep(retry_after)

                        continue

                    if response.status in (500, 503, 503):
                        await asyncio.sleep(retry * 2)
                        continue

                    error = self.errors.get(response.status, HTTPException)
                    raise error(data)

        raise RuntimeError('Could not complete the request for some unknown reason')

    async def search(self, query: str, type: str, market: str=None, limit: int=20, offset: int=0):
        params = {
            'q': query,
            'type': type,
            'limit': limit,
            'offset': offset
        }

        if market:
            params['market'] = market

        return await self.request('/search', 'GET', params=params)

    async def get_shows(self, ids: List[str], market: str=None):
        params = {
            'ids': ','.join(ids)
        }

        if market:
            params['market'] = market

        return await self.request('/shows', 'GET', params=params)

    async def get_show(self, id: str, market: str=None):
        params = {}
        url = f'/shows/{id}'

        if market:
            params['market'] = market

        return await self.request(url, 'GET', params=params)

    async def get_show_episodes(self, id: str, market: str=None, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset
        }
        url = f'/shows/{id}/episodes'

        if market:
            params['market'] = market

        return await self.request(url, 'GET', params=params)

    async def get_tracks(self, ids: List[str], market: str=None):
        params = {
            'ids': ','.join(ids)
        }

        if market:
            params['market'] = market

        return await self.request('/tracks', 'GET', params=params)

    async def get_track(self, id: str, market: str=None):
        params = {}
        url = f'/tracks/{id}'

        if market:
            params['market'] = market

        return await self.request(url, 'GET', params=params)

    async def get_tracks_audio_features(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/audio-features', 'GET', params=params)
    
    async def get_track_audio_features(self, id: str):
        return await self.request(f'/audio-features/{id}', 'GET')

    async def get_track_audio_analysis(self, id: str):
        return await self.request(f'/audio-analysis/{id}', 'GET')

    async def me(self):
        return await self.request('/me', 'GET')

    async def get_user(self, id: str):
        return await self.request(f'/users/{id}', 'GET')

    async def get_albums(self, ids: List[str], market: str=None):
        params = {
            'ids': ','.join(ids)
        }

        if market:
            params['market'] = market

        return await self.request('/albums', 'GET', params=params)

    async def get_album(self, id: str, market: str=None):
        url = f'/albums/{id}'
        params = {}

        if market:
            params['market'] = market

        return await self.request(url, 'GET', params=params)

    async def get_album_tracks(self, id: str, market: str=None, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset
        }
        url = f'/albums/{id}/tracks'

        if market:
            params['market'] = market

        return await self.request(url, 'GET', params=params)

    async def get_artists(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/artists', 'GET', params=params)

    async def get_artist(self, id: str):
        return await self.request(f'/artists/{id}', 'GET')

    async def get_artist_top_tracks(self, id: str, market: str=None):
        url = f'/artists/{id}/top-tracks'
        params = {}

        if market:
            params['market'] = market

        return await self.request(url, 'GET', params=params)

    async def get_artist_related_artists(self, id: str):
        return await self.request(f'/artists/{id}/related-artists', 'GET')

    async def get_artist_albums(
        self, 
        id: str, 
        include_groups: List[str]=None, 
        market: str=None, 
        limit: int=20, 
        offset: int=0
    ):
        params = {
            'limit': limit,
            'offset': offset
        }

        if market:
            params['market'] = market
        if include_groups:
            params['incldue_groups'] = ','.join(include_groups)

        return await self.request(f'/artists/{id}/albums', 'GET', params=params)

    async def get_new_releases(self, country: str=None, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset
        }

        if country:
            params['country'] = country

        return await self.request('/new-releases', 'GET', params=params)

    async def get_all_featured_playlists(
        self,
        country: str=None, 
        locale: str=None, 
        timestamp: str=None, 
        limit: int=20, 
        offset: int=0
    ):
        params = {
            'limit': limit,
            'offset': offset
        }

        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale
        if timestamp:
            params['timestamp'] = timestamp

        return await self.request('/browse/featured-playlists', 'GET', params=params)

    async def get_all_categories( 
        self,
        country: str=None, 
        locale: str=None, 
        limit: int=20, 
        offset: int=0
    ):
        params = {
            'limit': limit,
            'offset': offset
        }

        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale

        return await self.request('/browse/categories', 'GET', params=params)

    async def get_category(self, id: str, country: str=None, locale: str=None):
        params = {}
        url = f'/browse/categories/{id}'

        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale

        return await self.request(url, 'GET', params=params)

    async def get_category_playlists(
        self,
        id: str,
        country: str=None, 
        locale: str=None, 
        limit: int=20, 
        offset: int=0
    ):
        params = {
            'limit': limit,
            'offset': offset
        }

        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale

        return await self.request(f'/browse/categories/{id}/playlists', 'GET', params=params)

    async def get_recommendations(
        self,
        limit: int=20,
        market: str=None,
        seed_artists: List[str]=None,
        seed_genres: List[str]=None,
        seed_tracks: List[str]=None,
        min_acousticness: Union[int, float]=None,
        max_acousticness: Union[int, float]=None,
        target_acousticness: Union[int, float]=None,
        min_danceability: Union[int, float]=None,
        max_danceability: Union[int, float]=None,
        target_danceability: Union[int, float]=None,
        min_durantion_ms: int=None,
        max_durantion_ms: int=None,
        target_duration_ms: int=None,
        min_energy: Union[int, float]=None,
        max_energy: Union[int, float]=None,
        target_energy: Union[int, float]=None,
        min_intrumentalness: Union[int, float]=None,
        max_intrumentalness: Union[int, float]=None,
        target_intrumentalness: Union[int, float]=None,
        min_key: int=None,
        max_key: int=None,
        target_key: int=None,
        min_liveness: Union[int, float]=None,
        max_liveness: Union[int, float]=None,
        target_liveness: Union[int, float]=None,
        min_loudness: Union[int, float]=None,
        max_loudness: Union[int, float]=None,
        target_loudness: Union[int, float]=None,
        min_mode: int=None,
        max_mode: int=None,
        target_mode: int=None,
        min_popularity: int=None,
        max_popularity: int=None,
        target_popularity: int=None,
        min_speechiness: Union[int, float]=None,
        max_speechiness: Union[int, float]=None,
        target_speechiness: Union[int, float]=None,
        min_tempo: Union[int, float]=None,
        max_tempo: Union[int, float]=None,
        target_tempo: Union[int, float]=None,
        min_time_signature: int=None,
        max_time_signature: int=None,
        target_time_signature: int=None,
        min_valence: int=None,
        max_valence: int=None,
        target_valence: int=None
    ):
        params = {
            'limit': limit
        }

        if market:
            params['market'] = market
        if seed_artists:
            params['seed_artists'] = ','.join(seed_artists)
        if seed_genres:
            params['seed_genres'] = ','.join(seed_genres)
        if seed_tracks:
            params['seed_tracks'] = ','.join(seed_tracks)
        if min_acousticness:
            params['min_acousticness'] = min_acousticness
        if max_acousticness:
            params['max_acousticness'] = max_acousticness
        if target_acousticness:
            params['target_acousticness'] = target_acousticness
        if min_danceability:
            params['min_danceability'] = min_danceability
        if max_danceability:
            params['max_danceability'] = max_danceability
        if target_danceability:
            params['target_danceability'] = target_danceability
        if min_durantion_ms:
            params['min_durantion_ms'] = min_durantion_ms
        if max_durantion_ms:
            params['max_durantion_ms'] = max_durantion_ms
        if target_duration_ms:
            params['target_duration_ms'] = target_duration_ms
        if min_energy:
            params['min_energy'] = min_energy
        if max_energy:
            params['max_energy'] = max_energy
        if target_energy:
            params['target_energy'] = target_energy
        if min_intrumentalness:
            params['min_intrumentalness'] = min_intrumentalness
        if max_intrumentalness:
            params['max_intrumentalness'] = max_intrumentalness
        if target_intrumentalness:
            params['target_intrumentalness'] = target_intrumentalness
        if min_key:
            params['min_key'] = min_key
        if max_key:
            params['max_key'] = max_key
        if target_key:
            params['target_key'] = target_key
        if min_liveness:
            params['min_liveness'] = min_liveness
        if max_liveness:
            params['max_liveness'] = max_liveness
        if target_liveness:
            params['target_liveness'] = target_liveness
        if min_loudness:
            params['min_loudness'] = min_loudness
        if max_loudness:
            params['max_loudness'] = max_loudness
        if target_loudness:
            params['target_loudness'] = target_loudness
        if min_mode:
            params['min_mode'] = min_mode
        if max_mode:
            params['max_mode'] = max_mode
        if target_mode:
            params['target_mode'] = target_mode
        if min_popularity:
            params['min_popularity'] = min_popularity
        if max_popularity:
            params['max_popularity'] = max_popularity
        if target_popularity:
            params['target_popularity'] = target_popularity
        if min_speechiness:
            params['min_speechiness'] = min_speechiness
        if max_speechiness:
            params['max_speechiness'] = max_speechiness
        if target_speechiness:
            params['target_speechiness'] = target_speechiness
        if min_tempo:
            params['min_tempo'] = min_tempo
        if max_tempo:
            params['max_tempo'] = max_tempo
        if target_tempo:
            params['target_tempo'] = target_tempo
        if min_time_signature:
            params['min_time_signature'] = min_time_signature
        if max_time_signature:
            params['max_time_signature'] = max_time_signature
        if target_time_signature:
            params['target_time_signature'] = target_time_signature
        if min_valence:
            params['min_valence'] = min_valence
        if max_valence:
            params['max_valence'] = max_valence
        if target_valence:
            params['target_valence'] = target_valence
        
        return await self.request('/recommendations', 'GET', params=params)

    async def get_recommendation_genres(self):
        return await self.request('/recommendations/available-genre-seeds')

    async def get_episodes(self, ids: List[str], market: str=None):
        params = {
            'ids': ','.join(ids)
        }

        if market:
            params['market'] = market

        return await self.request('/episodes', 'GET', params=params)

    async def get_episode(self, id: int, market: str=None):
        params = {}

        if market:
            params['market'] = market
        
        return await self.request(f'/episodes/{id}', 'GET', params=params)
        
    async def follow_playlist(self, id: str, public: bool=True):
        payload = {
            'public': public
        }

        return await self.request(f'/playlists/{id}/followers', 'PUT', json=payload)

    async def unfollow_playlist(self, id: str):
        return await self.request(f'/playlists/{id}/followers', 'DELETE')
    
    async def users_follow_playlist(self, playlist_id: str, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request(f'/playlists/{playlist_id}/followers/contains', 'GET', params=params)
    
    async def get_user_followed_artists(self, after: str=None, limit: int=20):
        params = {
            'type': 'artist',
            'limit': limit
        }

        if after:
            params['after'] = after

        return await self.request('/me/following', 'GET', params=params)

    async def follow_users_or_artists(self, type: str, ids: List[str]):
        params = {
            'ids': ','.join(ids),
            'type': type
        }

        return await self.request('/me/following', 'PUT', json=params)

    async def unfollow_users_or_artists(self, type: str, ids: List[str]):
        params = {
            'ids': ','.join(ids),
            'type': type
        }

        return await self.request('/me/following', 'DELETE', params=params)

    async def get_following_state_for_users_or_atrists(self, type: str, ids: List[str]):
        params = {
            'ids': ','.join(ids),
            'type': type
        }

        return await self.request('/me/following/contains', 'GET', params=params)

    async def get_user_saved_albums(self, limit: int=20, offset: int=0, market: str=None):
        params = {
            'limit': limit,
            'offset': offset
        }

        if market:
            params['market'] = market

        return await self.request('/me/albums', 'GET', params=params)

    async def save_albums_for_current_user(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/albums', 'PUT', params=params)

    async def remove_albums_for_current_user(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/albums', 'DELETE', params=params)

    async def check_user_saved_albums(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/albums/contains', 'GET', params=params)

    async def get_user_saved_tracks(self, market: str=None, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset
        }

        if market:
            params['market'] = market

        return await self.request('/me/tracks', 'GET', params=params)

    async def save_tracks_for_user(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/tracks', 'PUT', params=params)

    async def remove_user_saved_tracks(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/tracks', 'DELETE', params=params)

    async def check_user_saved_tracks(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/tracks/contains', 'GET', params=params)

    async def get_user_saved_episodes(self, limit: int=20, offset: int=0, market: str=None):
        params = {
            'limit': limit,
            'offset': offset
        }

        if market:
            params['market'] = market

        return await self.request('/me/episodes', 'GET', params=params)

    async def save_episodes_for_user(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/episodes', 'PUT', params=params)

    async def remove_user_saved_episodes(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/episodes', 'DELETE', params=params)

    async def check_user_saved_episodes(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/episodes/contains', 'GET', params=params)

    async def get_user_saved_shows(self):
        return await self.request('/me/shows', 'GET')

    async def save_shows_for_user(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/shows', 'PUT', params=params)

    async def remove_shows_for_user(self, ids: List[str], market: str=None):
        params = {
            'ids': ','.join(ids)
        }

        if market:
            params['market'] = market

        return await self.request('/me/shows', 'DELETE', params=params)

    async def check_user_saved_shows(self, ids: List[str]):
        params = {
            'ids': ','.join(ids)
        }

        return await self.request('/me/shows/contains', 'GET', params=params)

    async def get_available_markets(self):
        return await self.request('/markets', 'GET')

    async def get_user_top_tracks_or_artist(self, type: str, time_range: str=None, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset,
            'time_range': time_range or 'medium_term'
        }

        return await self.request(f'/me/top/{type}', 'GET', params=params)

    async def get_user_current_playback(self, market: str=None, additional_types: List[str]=None):
        params = {
            'additional_types': ','.join(additional_types or ['track'])
        }

        if market:
            params['market'] = market

        return await self.request('/me/player', 'GET', params=params)

    async def transfer_user_playback(self, device_ids: List[str], play: bool=None):
        data = {
            'device_ids': ','.join(device_ids)
        }

        if play is not None:
            data['play'] = play

        return await self.request('/me/player', 'PUT', json=data)

    async def get_user_devices(self):
        return await self.request('/me/player/devices', 'GET')

    async def get_user_currently_playing_track(self, market: str=None, additional_types: List[str]=None):
        params = {
            'additional_types': ','.join(additional_types or ['track'])
        }

        if market:
            params['market'] = market

        return await self.request('/me/player/currently-playing', 'GET', params=params)

    async def start_or_resume_user_playback(
        self, 
        device_id: str=None, 
        context_uri: str=None, 
        uris: List[str]=None, 
        offset: int=None,
        position_ms: int=None
    ):
        params = {}
        if device_id:
            params['device_id'] = device_id

        data = {}
        if context_uri:
            data['context_uri'] = context_uri
        if uris:
            data['uris'] = uris
        if offset:
            data['offset'] = offset
        if position_ms:
            data['position_ms'] = position_ms

        return await self.request('/me/player/play', 'PUT', json=data, params=params)

    async def pause_user_playback(self, device_id: str=None):
        params = {}
        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/pause', 'PUT', params=params)

    async def skip_user_playback(self, next: bool=True, device_id: str=None):
        url = '/me/player/next'
        if not next:
            url = '/me/player/previous'

        params = {}
        if device_id:
            params['device_id'] = device_id

        return await self.request(url, 'PUT', params=params)

    async def seek_to_position_in_currently_playing_track(self, position_ms: int, device_id: str=None):
        params = {
            'position_ms': position_ms
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/seek', 'PUT', params=params)

    async def set_repeat_on_user_playback(self, state: str, device_id: str=None):
        params = {
            'state': state
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/repeat', 'PUT', params=params)

    async def set_volume_for_user_playback(self, volume_percentage: int, device_id: str=None):
        params = {
            'volume_percentage': volume_percentage
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/volume', 'PUT', params=params)

    async def toggle_shuffle_for_user_playback(self, state: bool, device_id: str=None):
        params = {
            'state': state
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/shuffle', 'PUT', params=params)

    async def get_user_recently_played_tracks(self, limit: int=20, after: int=None, before: int=None):
        params = {
            'limit': limit
        }

        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.request('/me/player/recently-played', 'GET', params=params)

    async def add_item_to_queue(self, uri: str, device_id: str=None):
        params = {
            'uri': uri
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/queue', 'POST', params=params)

    async def get_list_of_current_user_playlists(self, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset
        }

    async def get_list_of_a_user_playlists(self, user_id: str, limit: int=20, offset: int=0):
        params = {
            'limit': limit,
            'offset': offset
        }

        return await self.request(f'/users/{user_id}/playlists', 'GET', params=params)

    async def create_playlist(
        self, 
        user_id: str, 
        name: str, 
        public: bool=True, 
        collaborative: bool=False,
        description: str=None
    ):
        data = {
            'name': name,
            'public': public,
            'collaborative': collaborative
        }

        if description:
            data['description'] = description

        return await self.request(f'/users/{user_id}/playlists', 'POST', json=data)
        
    async def get_playlist(
        self, 
        id: str, 
        market: str=None, 
        fields: List[str]=None, 
        additional_types: List[str]=None
    ):
        additional_types = ','.join(additional_types or ['track'])
        params = {
            'additional_types': additional_types
        }

        if market:
            params['market'] = market
        if fields:
            params['fields'] = ','.join(fields)

        return await self.request(f'/playlists/{id}', 'GET', params=params)

    async def change_playlist_details(
        self, 
        id: str, 
        name: str=None, 
        public: bool=None, 
        collaborative: bool=None, 
        description: bool=None
    ):
        data = {}

        if name:
            data['name'] = name
        if public is not None:
            data['public'] = public
        if collaborative is not None:
            data['collaborative'] = collaborative
        if description:
            data['description'] = description

        return await self.request(f'/playlists/{id}', 'PUT', json=data)

    async def get_playlist_items(
        self,
        id: str,
        limit: int=20,
        offset: int=0,
        market: str=None, 
        fields: List[str]=None, 
        additional_types: List[str]=None
    ):
        additional_types = ','.join(additional_types or ['track'])
        params = {
            'additional_types': additional_types,
            'limit': limit,
            'offset': offset
        }

        if market:
            params['market'] = market
        if fields:
            params['fields'] = ','.join(fields)

        return await self.request(f'/playlists/{id}/tracks', 'GET', params=params)

    async def add_items_to_playlist(
        self,
        id: str,
        position: int=None,
        uris: List[str]=None,
    ):
        params = {}

        if position:
            params['position'] = position
        if uris:
            params['uris'] = ','.join(uris)

        return await self.request(f'/playlists/{id}/tracks', 'POST', params=params)

    async def remove_items_from_playlist(
        self,
        id: str,
        tracks: List[Dict[str, Any]]=None
    ):
        data = {}
        if tracks:
            data['tracks'] = tracks

        return await self.request(f'/playlists/{id}/tracks', 'DELETE', json=data)


        