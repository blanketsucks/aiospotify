from typing import Any, Dict, List, Optional
import aiohttp
import asyncio
import urllib.parse
import base64
import datetime

from .errors import Forbidden, HTTPException, NotFound, Unauthorized, BadRequest
    
class Authentication:
    __slots__ = (
        'client_id',
        'client_secret',
        'session',
        'expires_at',
        '_refresh_token',
        'token',
    )

    URL = 'https://accounts.spotify.com/api/token'

    def __init__(self, client_id: str, client_secret: str, session: aiohttp.ClientSession) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session

        self.expires_at: Optional[datetime.datetime] = None
        self._refresh_token: Optional[str] = None
        self.token: Optional[str] = None

    def is_expired(self):
        if not self.expires_at:
            return True

        return datetime.datetime.utcnow() > self.expires_at

    def is_oauth2(self):
        return self._refresh_token is not None

    def build_basic_token(self):
        client_id = urllib.parse.quote(self.client_id)
        client_secret = urllib.parse.quote(self.client_secret)

        token = base64.b64encode('{}:{}'.format(client_id, client_secret).encode('utf8'))
        token = token.decode('utf-8')

        return token

    async def fetch_token(self) -> str:
        if self.is_expired():
            if self.is_oauth2():
                return await self.fetch_refresh_token()
            else:
                return await self.fetch_access_token()

        if self.token is not None:
            return self.token

        return await self.fetch_access_token()

    async def fetch_access_token(self) -> str:
        data = {
            'grant_type': 'client_credentials'
        }

        token = self.build_basic_token()
        headers = {
            'Authorization': 'Basic ' + token,
        }

        async with self.session.post(self.URL, headers=headers, data=data) as response:
            data: Dict[str, Any] = await response.json()

            self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=data['expires_in'])
            self.token = data['access_token']
            self._refresh_token = data.get('refresh_token')

        return self.token

    async def fetch_refresh_token(self) -> str:
        data = {
            'refresh_token': self.token,
            'grant_type': 'refresh_token'
        }

        async with self.session.post(self.URL, data=data) as response:
            data: Dict[str, Any] = await response.json()

            self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=data['expires_in'])
            self.token = data['access_token']
            self._refresh_token = data.get('refresh_token')
        
        return self.token

class HTTPClient:
    URL = 'https://api.spotify.com/v1'
    def __init__(
        self, 
        client_id: str, 
        client_secret: str,
        *, 
        loop: asyncio.AbstractEventLoop, 
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.loop = loop
        self.session = session or aiohttp.ClientSession(loop=self.loop)
        self.auth = Authentication(client_id, client_secret, self.session)
        self.errors = {
            401: Unauthorized,
            403: Forbidden,
            404: NotFound,
            400: BadRequest
        }

        self.lock = asyncio.Lock()

    def update_params(self, **kwargs: Any) -> Dict[str, Any]:
        return {key: value for key, value in kwargs.items() if value is not None}

    async def read(self, url: str):
        async with self.session.get(url) as response:
            return await response.read()

    async def request(self, path: str, method: str, **kwargs) -> Dict[str, Any]:
        token = await self.auth.fetch_token()

        url = self.URL + path
        headers = {
            'Authorization': 'Bearer ' + token
        }

        async with self.lock:
            async with self.session.request(method, url, headers=headers, **kwargs) as response:
                data = await response.json(encoding='utf-8')

                if 300 > response.status >= 200:
                    return data

                if response.status == 429:
                    retry_after = float(response.headers['Retry-After'])
                    await asyncio.sleep(retry_after)

                    return await self.request(path, method, **kwargs)

                error = self.errors.get(response.status, HTTPException)
                raise error(data)

        raise RuntimeError('Unreachable code')

    async def search(
        self, query: str, type: str, market: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        params = self.update_params(query=query, type=type, market=market, limit=limit, offset=offset)
        return await self.request('/search', 'GET', params=params)

    async def get_shows(self, ids: List[str], market: Optional[str] = None):
        values = ','.join(ids)
        params = self.update_params(ids=values, market=market)

        return await self.request('/shows', 'GET', params=params)

    async def get_show(self, id: str, market: Optional[str] = None):
        params = self.update_params(market=market)
        return await self.request(f'/shows/{id}', 'GET', params=params)

    async def get_show_episodes(
        self, id: str, market: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        params = self.update_params(market=market, limit=limit, offset=offset)
        return await self.request(f'/shows/{id}/episodes', 'GET', params=params)

    async def get_tracks(self, ids: List[str], market: Optional[str] = None):
        params = {'ids': ','.join(ids)}

        if market:
            params['market'] = market

        return await self.request('/tracks', 'GET', params=params)

    async def get_track(self, id: str, market: Optional[str] = None):
        params = self.update_params(market=market)
        return await self.request(f'/tracks/{id}', 'GET', params=params)

    async def get_tracks_audio_features(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/audio-features', 'GET', params=params)
    
    async def get_track_audio_features(self, id: str):
        return await self.request(f'/audio-features/{id}', 'GET')

    async def get_track_audio_analysis(self, id: str):
        return await self.request(f'/audio-analysis/{id}', 'GET')

    async def me(self):
        return await self.request('/me', 'GET')

    async def get_user(self, id: str):
        return await self.request(f'/users/{id}', 'GET')

    async def get_albums(self, ids: List[str], market: Optional[str] = None):
        values = ','.join(ids)
        params = self.update_params(ids=values, market=market)

        return await self.request('/albums', 'GET', params=params)

    async def get_album(self, id: str, market: Optional[str] = None):
        params = self.update_params(market=market)
        return await self.request(f'/albums/{id}', 'GET', params=params)

    async def get_album_tracks(
        self, id: str, market: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        params = self.update_params(market=market, limit=limit, offset=offset)
        return await self.request(f'/albums/{id}/tracks', 'GET', params=params)

    async def get_artists(self, ids: List[str]) -> Dict[str, Any]:
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/artists', 'GET', params=params)

    async def get_artist(self, id: str) -> Dict[str, Any]:
        return await self.request(f'/artists/{id}', 'GET')

    async def get_artist_top_tracks(self, id: str, market: Optional[str] = None):
        params = self.update_params(market=market)
        return await self.request(f'/artists/{id}/top-tracks', 'GET', params=params)

    async def get_artist_related_artists(self, id: str):
        return await self.request(f'/artists/{id}/related-artists', 'GET')

    async def get_artist_albums(
        self, 
        id: str, 
        include_groups: Optional[List[str]] = None, 
        market: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ):
        params = self.update_params(market=market, limit=limit, offset=offset)
        if include_groups:
            params['include_groups'] = ','.join(include_groups)

        return await self.request(f'/artists/{id}/albums', 'GET', params=params)

    async def get_new_releases(self, country: Optional[str] = None, limit: int = 20, offset: int = 0):
        params = self.update_params(country=country, limit=limit, offset=offset)
        return await self.request('/new-releases', 'GET', params=params)

    async def get_all_featured_playlists(
        self,
        country: Optional[str] = None, 
        locale: Optional[str] = None, 
        timestamp: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        params = self.update_params(
            country=country, locale=locale, timestamp=timestamp, limit=limit, offset=offset
        )
        return await self.request('/browse/featured-playlists', 'GET', params=params)

    async def get_all_categories( 
        self,
        country: Optional[str] = None, 
        locale: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        params = self.update_params(country=country, locale=locale, limit=limit, offset=offset)
        return await self.request('/browse/categories', 'GET', params=params)

    async def get_category(self, id: str, country: Optional[str] = None, locale: Optional[str] = None):
        params = self.update_params(country=country, locale=locale)
        return await self.request(f'/browse/categories/{id}', 'GET', params=params)

    async def get_category_playlists(
        self,
        id: str,
        country: Optional[str] = None, 
        locale: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        params = self.update_params(country=country, locale=locale, limit=limit, offset=offset)
        return await self.request(f'/browse/categories/{id}/playlists', 'GET', params=params)

    async def get_recommendations(
        self,
        limit: int = 20,
        market: Optional[str] = None,
        seed_artists: Optional[List[str]] = None,
        seed_genres: Optional[List[str]] = None,
        seed_tracks: Optional[List[str]] = None,
        min_acousticness: Optional[float] = None,
        max_acousticness: Optional[float] = None,
        target_acousticness: Optional[float] = None,
        min_danceability: Optional[float] = None,
        max_danceability: Optional[float] = None,
        target_danceability: Optional[float] = None,
        min_durantion_ms: Optional[int] = None,
        max_durantion_ms: Optional[int] = None,
        target_duration_ms: Optional[int] = None,
        min_energy: Optional[float] = None,
        max_energy: Optional[float] = None,
        target_energy: Optional[float] = None,
        min_intrumentalness: Optional[float] = None,
        max_intrumentalness: Optional[float] = None,
        target_intrumentalness: Optional[float] = None,
        min_key: Optional[int] = None,
        max_key: Optional[int] = None,
        target_key: Optional[int] = None,
        min_liveness: Optional[float] = None,
        max_liveness: Optional[float] = None,
        target_liveness: Optional[float] = None,
        min_loudness: Optional[float] = None,
        max_loudness: Optional[float] = None,
        target_loudness: Optional[float] = None,
        min_mode: Optional[int] = None,
        max_mode: Optional[int] = None,
        target_mode: Optional[int] = None,
        min_popularity: Optional[int] = None,
        max_popularity: Optional[int] = None,
        target_popularity: Optional[int] = None,
        min_speechiness: Optional[float] = None,
        max_speechiness: Optional[float] = None,
        target_speechiness: Optional[float] = None,
        min_tempo: Optional[float] = None,
        max_tempo: Optional[float] = None,
        target_tempo: Optional[float] = None,
        min_time_signature: Optional[int] = None,
        max_time_signature: Optional[int] = None,
        target_time_signature: Optional[int] = None,
        min_valence: Optional[int] = None,
        max_valence: Optional[int] = None,
        target_valence: Optional[int] = None
    ) -> Dict[str, Any]:
        params = self.update_params(
            market=market,
            limit=limit,
            seed_artists=seed_artists,
            seed_genres=seed_genres,
            seed_tracks=seed_tracks,
            min_acousticness=min_acousticness,
            max_acousticness=max_acousticness,
            target_acousticness=target_acousticness,
            min_danceability=min_danceability,
            max_danceability=max_danceability,
            target_danceability=target_danceability,
            min_durantion_ms=min_durantion_ms,
            max_durantion_ms=max_durantion_ms,
            target_duration_ms=target_duration_ms,
            min_energy=min_energy,
            max_energy=max_energy,
            target_energy=target_energy,
            min_intrumentalness=min_intrumentalness,
            max_intrumentalness=max_intrumentalness,
            target_intrumentalness=target_intrumentalness,
            min_key=min_key,
            max_key=max_key,
            target_key=target_key,
            min_liveness=min_liveness,
            max_liveness=max_liveness,
            target_liveness=target_liveness,
            min_loudness=min_loudness,
            max_loudness=max_loudness,
            target_loudness=target_loudness,
            min_mode=min_mode,
            max_mode=max_mode,
            target_mode=target_mode,
            min_popularity=min_popularity,
            max_popularity=max_popularity,
            target_popularity=target_popularity,
            min_speechiness=min_speechiness,
            max_speechiness=max_speechiness,
            target_speechiness=target_speechiness,
            min_tempo=min_tempo,
            max_tempo=max_tempo,
            target_tempo=target_tempo,
            min_time_signature=min_time_signature,
            max_time_signature=max_time_signature,
            target_time_signature=target_time_signature,
            min_valence=min_valence,
            max_valence=max_valence,
            target_valence=target_valence
        )

        return await self.request('/recommendations', 'GET', params=params)
        

    async def get_recommendation_genres(self):
        return await self.request('/recommendations/available-genre-seeds', 'GET')

    async def get_episodes(self, ids: List[str], market: Optional[str] = None):
        values = ','.join(ids)
        params = self.update_params(market=market, ids=values)

        return await self.request('/episodes', 'GET', params=params)

    async def get_episode(self, id: int, market: Optional[str] = None):
        params = self.update_params(market=market)
        return await self.request(f'/episodes/{id}', 'GET', params=params)
        
    async def follow_playlist(self, id: str, public: bool = True):
        payload = {'public': public}
        return await self.request(f'/playlists/{id}/followers', 'PUT', json=payload)

    async def unfollow_playlist(self, id: str):
        return await self.request(f'/playlists/{id}/followers', 'DELETE')
    
    async def users_follow_playlist(self, playlist_id: str, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request(f'/playlists/{playlist_id}/followers/contains', 'GET', params=params)
    
    async def get_user_followed_artists(self, after: Optional[str] = None, limit: int = 20):
        params = self.update_params(after=after, limit=limit, type='artist')

        return await self.request('/me/following', 'GET', params=params)

    async def follow_users_or_artists(self, type: str, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(type=type, ids=values)

        return await self.request('/me/following', 'PUT', json=params)

    async def unfollow_users_or_artists(self, type: str, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(type=type, ids=values)

        return await self.request('/me/following', 'DELETE', params=params)

    async def get_following_state_for_users_or_atrists(self, type: str, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(type=type, ids=values)

        return await self.request('/me/following/contains', 'GET', params=params)

    async def get_user_saved_albums(self, limit: int = 20, offset: int = 0, market: Optional[str] = None):
        params = self.update_params(limit=limit, offset=offset, market=market)
        return await self.request('/me/albums', 'GET', params=params)

    async def save_albums_for_current_user(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/albums', 'PUT', params=params)

    async def remove_albums_for_current_user(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/albums', 'DELETE', params=params)

    async def check_user_saved_albums(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/albums/contains', 'GET', params=params)

    async def get_user_saved_tracks(self, market: Optional[str] = None, limit: int = 20, offset: int = 0):
        params = self.update_params(market=market, limit=limit, offset=offset)
        return await self.request('/me/tracks', 'GET', params=params)

    async def save_tracks_for_user(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/tracks', 'PUT', params=params)

    async def remove_user_saved_tracks(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/tracks', 'DELETE', params=params)

    async def check_user_saved_tracks(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/tracks/contains', 'GET', params=params)

    async def get_user_saved_episodes(self, limit: int = 20, offset: int = 0, market: Optional[str] = None):
        params = self.update_params(market=market, limit=limit, offset=offset)
        return await self.request('/me/episodes', 'GET', params=params)

    async def save_episodes_for_user(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/episodes', 'PUT', params=params)

    async def remove_user_saved_episodes(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/episodes', 'DELETE', params=params)

    async def check_user_saved_episodes(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/episodes/contains', 'GET', params=params)

    async def get_user_saved_shows(self):
        return await self.request('/me/shows', 'GET')

    async def save_shows_for_user(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/shows', 'PUT', params=params)

    async def remove_shows_for_user(self, ids: List[str], market: Optional[str] = None):
        values = ','.join(ids)
        params = self.update_params(ids=values, market=market)

        return await self.request('/me/shows', 'DELETE', params=params)

    async def check_user_saved_shows(self, ids: List[str]):
        values = ','.join(ids)
        params = self.update_params(ids=values)

        return await self.request('/me/shows/contains', 'GET', params=params)

    async def get_available_markets(self):
        return await self.request('/markets', 'GET')

    async def get_user_top_tracks_or_artist(self, type: str, time_range: Optional[str] = None, limit: int = 20, offset: int = 0):
        time_range = time_range or 'medium_term'
        params = self.update_params(time_range=time_range, limit=limit, offset=offset)

        return await self.request(f'/me/top/{type}', 'GET', params=params)

    async def get_user_current_playback(self, market: Optional[str] = None, additional_types: Optional[List[str]] = None):
        values = ','.join(additional_types or ['track'])
        params = self.update_params(market=market, additional_types=values)

        return await self.request('/me/player', 'GET', params=params)

    async def transfer_user_playback(self, device_ids: List[str], play: Optional[bool] = None):
        values = ','.join(device_ids)
        data = self.update_params(device_ids=values, play=play)

        return await self.request('/me/player', 'PUT', json=data)

    async def get_user_devices(self):
        return await self.request('/me/player/devices', 'GET')

    async def get_user_currently_playing_track(self, market: Optional[str] = None, additional_types: Optional[List[str]] = None):
        values = ','.join(additional_types or ['track'])
        params = self.update_params(market=market, additional_types=values)

        return await self.request('/me/player/currently-playing', 'GET', params=params)

    async def start_or_resume_user_playback(
        self, 
        device_id: Optional[str] = None, 
        context_uri: Optional[str] = None, 
        uris: Optional[List[str]] = None, 
        offset: Optional[int] = None,
        position_ms: Optional[int] = None
    ):
        params = self.update_params(device_id=device_id)
        data = self.update_params(context_uri=context_uri, uris=uris, offset=offset, position_ms=position_ms)

        return await self.request('/me/player/play', 'PUT', json=data, params=params)

    async def pause_user_playback(self, device_id: Optional[str] = None):
        params = self.update_params(device_id=device_id)
        return await self.request('/me/player/pause', 'PUT', params=params)

    async def skip_user_playback(self, next: bool = True, device_id: Optional[str] = None):
        url = '/me/player/next'
        if not next:
            url = '/me/player/previous'

        params = self.update_params(device_id=device_id)
        return await self.request(url, 'PUT', params=params)

    async def seek_to_position_in_currently_playing_track(self, position_ms: int, device_id: Optional[str] = None):
        params: Dict[str, Any] = {
            'position_ms': position_ms
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/seek', 'PUT', params=params)

    async def set_repeat_on_user_playback(self, state: str, device_id: Optional[str] = None):
        params = {
            'state': state
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/repeat', 'PUT', params=params)

    async def set_volume_for_user_playback(self, volume_percentage: int, device_id: Optional[str] = None):
        params: Dict[str, Any] = {
            'volume_percentage': volume_percentage
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/volume', 'PUT', params=params)

    async def toggle_shuffle_for_user_playback(self, state: bool, device_id: Optional[str] = None):
        params: Dict[str, Any] = {
            'state': state
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/shuffle', 'PUT', params=params)

    async def get_user_recently_played_tracks(self, limit: int = 20, after: Optional[int] = None, before: Optional[int] = None):
        params = {
            'limit': limit
        }

        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.request('/me/player/recently-played', 'GET', params=params)

    async def add_item_to_queue(self, uri: str, device_id: Optional[str] = None):
        params = {
            'uri': uri
        }

        if device_id:
            params['device_id'] = device_id

        return await self.request('/me/player/queue', 'POST', params=params)

    async def get_user_playlists(self, user_id: str, limit: int = 20, offset: int = 0):
        params = {
            'limit': limit,
            'offset': offset
        }

        return await self.request(f'/users/{user_id}/playlists', 'GET', params=params)

    async def create_playlist(
        self, 
        user_id: str, 
        name: str,
        public: bool = True, 
        collaborative: bool = False,
        description: Optional[str] = None
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
        market: Optional[str] = None, 
        fields: Optional[List[str]] = None, 
        additional_types: Optional[List[str]] = None
    ):
        types = ','.join(additional_types or ['track'])
        params = {
            'additional_types': types
        }

        if market:
            params['market'] = market
        if fields:
            params['fields'] = ','.join(fields)

        return await self.request(f'/playlists/{id}', 'GET', params=params)

    async def change_playlist_details(
        self, 
        id: str, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
        public: Optional[bool] = None, 
        collaborative: Optional[bool] = None, 
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
        limit: int = 20,
        offset: int = 0,
        market: Optional[str] = None, 
        fields: Optional[List[str]] = None, 
        additional_types: Optional[List[str]] = None
    ):
        additional_types = additional_types or ['track']
        params = {
            'additional_types': ','.join(additional_types),
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
        position: Optional[int] = None,
        uris: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        urls = ','.join(uris or [])
        params = self.update_params(position=position, uris=urls)

        return await self.request(f'/playlists/{id}/tracks', 'POST', params=params)

    async def remove_items_from_playlist(
        self,
        id: str,
        tracks: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        data = {}
        if tracks:
            data['tracks'] = tracks

        return await self.request(f'/playlists/{id}/tracks', 'DELETE', json=data)

    async def get_playlist_cover_image(self, id: str):
        return await self.request(f'/playlists/{id}/images', 'GET')
