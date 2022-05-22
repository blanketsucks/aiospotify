from __future__ import annotations

from typing import List, Optional, Tuple, Union
from urllib.parse import urlparse
import asyncio
import aiohttp
import sys
import re

from .http import HTTPClient
from .user import CurrentUser, User
from .track import Track
from .enums import ObjectType
from .search import SearchResult
from .playlist import Playlist
from .show import Show

__all__ = (
    'SpotifyClient',
)

PY310 = sys.version_info >= (3, 10)

SPOTIFY_URL_REGEX = re.compile(r'https:\/\/(open.spotify.com|play.spotify.com)\/(?P<type>user|track|album|artist|playlist|show)\/(?P<id>\w*)')
SPOTIFY_URI_REGEX = re.compile(r'^spotify:(?P<type>user|track|album|artist|playlist|show):(?P<id>.*)$')

def get_event_loop(loop: Optional[asyncio.AbstractEventLoop] = None) -> asyncio.AbstractEventLoop:
    if loop is not None:
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise TypeError('loop must be an instance of asyncio.AbstractEventLoop')

        return loop

    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        if not PY310:
            return asyncio.get_event_loop()

        raise

class SpotifyClient:
    def __init__(
        self, 
        client_id: str, 
        client_secret: str, 
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] =None,
    ) -> None:
        self.http = HTTPClient(
            client_id=client_id, 
            client_secret=client_secret, 
            loop=get_event_loop(loop),
            session=session,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    @classmethod
    def from_token(cls, token: str, **kwargs) -> SpotifyClient:
        self = cls(None, None, **kwargs) # type: ignore

        self.http.auth.token = token
        return self
    
    @property
    def loop(self):
        return self.http.loop

    def parse_url(self, url: str) -> Tuple[str, str]:
        match = SPOTIFY_URL_REGEX.match(url)
        if not match:
            raise ValueError(f'{url!r} is not a valid spotify url')
    
        return match.group('type'), match.group('id')

    def parse_uri(self, uri: str):
        match = SPOTIFY_URI_REGEX.match(uri)
        if not match:
            raise ValueError(f'{uri!r} is not a valid spotify uri')

        return match.group('type'), match.group('id')

    def parse_argument(self, argument: str, *, type: str) -> str:
        try:
            typ, id = self.parse_uri(argument)
        except ValueError:
            try:
                typ, id = self.parse_url(argument)
            except ValueError:
                return argument

        if typ != type:
            raise ValueError(f'{argument!r} is not a valid {type!r} uri')

        return id

    async def search(
        self, 
        query: str, 
        *, 
        types: Optional[List[ObjectType]] = None, 
        limit: int = 20, 
        offset: int = 0, 
        market: Optional[str] = None
    ) -> SearchResult:
        types = types or [ObjectType.TRACK, ObjectType.ALBUM, ObjectType.ARTIST]
        values = ','.join([type.value for type in types])

        data = await self.http.search(query, values, limit=limit, offset=offset, market=market)
        return SearchResult(data, self.http)
        
    async def fetch_current_user(self) -> CurrentUser:
        data = await self.http.me()
        return CurrentUser(data, self.http)

    async def fetch_tracks(self, uris: List[str], *, market: Optional[str] = None) -> List[Track]:
        ids = [self.parse_argument(uri, type='track') for uri in uris]
        data = await self.http.get_tracks(ids=ids, market=market)

        return [Track(item, self.http) for item in data['tracks']]

    async def fetch_track(self, uri: str, *, market: Optional[str] = None) -> Track:
        id = self.parse_argument(uri, type='track')
        data = await self.http.get_track(id, market=market)

        return Track(data, self.http)

    async def fetch_user(self, uri: str):
        id = self.parse_argument(uri, type='user')
        data = await self.http.get_user(id)

        return User(data, self.http)

    async def fetch_playlist(self, uri: str):
        id = self.parse_argument(uri, type='playlist')
        data = await self.http.get_playlist(id)

        return Playlist(data, self.http)

    async def fetch_shows(self, *uris: str, market: Optional[str] = None) -> List[Show]:
        ids = [self.parse_argument(uri, type='show') for uri in uris]

        data = await self.http.get_shows(ids, market=market)
        return [Show(item, self.http) for item in data['items']]
    
    async def fetch_show(self, uri: str, *, market: Optional[str] = None) -> Show:
        id = self.parse_argument(uri, type='show')
        data = await self.http.get_show(id, market)

        return Show(data, self.http)

    async def close(self):
        await self.http.session.close()