from typing import List, Union
from urllib.parse import urlparse

from .http import HTTPClient

from .user import CurrentUser, User
from .track import Track
from .state import CacheState
from .enums import ObjectType
from .search import SearchResult

__all__ = (
    'SpotifyClient',
)

class SpotifyClient:
    def __init__(self, client_id: Union[str, int], client_secret: str, **kwargs) -> None:
        self.http = HTTPClient(client_id, client_secret, **kwargs)
        self._state = CacheState(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    def build_oauth_url(self, scopes: List[str]=None):
        url = self.http.auth.build_oauth_url(scopes)
        return url

    @classmethod
    def from_token(cls, token: str, **kwargs) -> 'SpotifyClient':
        self = cls(None, None, **kwargs)
        self.http.auth.token = token

        return self
    
    @property
    def loop(self):
        return self.http.loop

    def parse_url(self, url: str):
        parsed = urlparse(url)
        if parsed.netloc == 'open.spotify.com':
            split = parsed.path.split('/')
            _, type, id = split

            return type, id
    
        raise ValueError('Not a valid Spotify URL')

    def parse_urn(self, uri: str):
        split = uri.split(':')
        if len(split) == 3:
            _, type, id = split
            return type, id

        raise ValueError('Not a valid Spotify URI')

    def parse_argument(self, argument: str):
        try:
            return self.parse_urn(argument)
        except ValueError:
            try:
                return self.parse_url(argument)
            except ValueError:
                return None, argument

    def verify_argument(self, argument: str, required: str):
        type, id = self.parse_argument(argument)
        if not type:
            return id

        if type != required:
            raise ValueError('Invalid uri argument')

        return id

    def get_track(self, uri: str):
        return self._state.get_track_from_uri(uri)
        
    def get_playlist(self, uri: str):
        return self._state.get_playlist_from_uri(uri)

    def get_user(self, uri: str):
        return self._state.get_user_from_uri(uri)

    async def search(
        self, 
        q: str, 
        types: List[ObjectType]=None, 
        *, 
        limit: int=20, 
        offset: int=0, 
        market: str=None
    ) -> SearchResult:
        values = types or [ObjectType.TRACK, ObjectType.ALBUM, ObjectType.ARTIST]
        types = ','.join([type.value for type in values])

        data = await self.http.search(q, types, limit=limit, offset=offset, market=market)

        return SearchResult(data, self._state)
        
    async def fetch_current_user(self) -> CurrentUser:
        data = await self.http.me()
        return CurrentUser(data, self._state)

    async def fetch_track(self, uri: str, *, market: str=None) -> Track:
        if (track := self.get_track(uri)):
            return track

        id = self.verify_argument(uri, 'track')
        data = await self.http.get_track(id, market=market)

        return self._state.add_track(
            track=Track(data, self._state)
        )

    async def fetch_user(self, uri: str):
        if (user := self.get_user(uri)):
            return user

        id = self.verify_argument(uri, 'user')
    
        data = await self.http.get_user(id)
        return self._state.add_user(
            user=User(data)
        )

    async def fetch_playlist(self, uri: str):
        id = self.verify_argument(uri, 'playlist')
        data = await self.http.get_playlist(id)

    async def close(self):
        await self.http.session.close()