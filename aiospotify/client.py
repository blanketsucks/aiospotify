import asyncio
from typing import List, Optional, Union
from urllib.parse import urlparse

import aiohttp

from .http import HTTPClient
from .user import CurrentUser, User
from .track import Track
from .state import CacheState
from .enums import ObjectType
from .search import SearchResult
from .playlist import Playlist
from .show import Show

__all__ = (
    'SpotifyClient',
)

class SpotifyClient:
    """
    A spotify client.
    """
    def __init__(
        self, 
        client_id: str, 
        client_secret: str, 
        *,
        loop: asyncio.AbstractEventLoop=None,
        session: aiohttp.ClientSession=None,
        oauth2: bool=True
    ) -> None:
        """
        SpotifyClient constructor
        
        Args:
            client_id: Spotify application client id.
            client_secret: Spotify application client secret.
            loop: The asyncio event loop to use with the HTTP session.
            session: The aiohttp session to use.
            oauth2: Whether to use OAuth2 authentication. If set to True, this starts a server 
                in the background waiting for a request to come in. The person performing that request 
                should you doing it through the oauth2 url that you can get through the build_oauth_url method. 
                After that it retreives the oauth2 token and uses it. If you set this to to True 
                and you don't authenticate it will use the client credentials flow for operations in the meanwhile.
        """
        self.http = HTTPClient(
            client_id=client_id, 
            client_secret=client_secret, 
            loop=loop,
            session=session,
            oauth2=oauth2
        )
        self._state = CacheState(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    def build_oauth_url(self, scopes: List[str]=None) -> Optional[str]:
        """
        Builds an oauth2 url. The redirect_uri is set to 'http://localhost:8080/callback'.

        Args:
            scopes: A list of scopes to request.
        
        """
        if not self.http.client_id:
            return None

        url = self.http.auth.build_oauth_url(scopes)
        return url

    @classmethod
    def from_token(cls, token: str, **kwargs) -> 'SpotifyClient':
        """
        Creates a client from an access token.

        Args:
            token: The access token.
            **kwargs: The keyword arguments to pass to the constructor.
        """
        kwargs.pop('oauth2', None)
        self = cls(None, None, oauth2=False, **kwargs)

        self.http.auth.token = token
        return self
    
    @property
    def loop(self):
        """
        Returns:
            The event loop used by the client.
        """
        return self.http.loop

    def parse_url(self, url: str):
        """
        Parses the given URL into a tuple of type and id.

        Args:
            url: The URL to parse.

        Raises:
            ValueError: If the URL is not a valid Spotify URL.
        """
        parsed = urlparse(url)
        if parsed.netloc == 'open.spotify.com':
            split = parsed.path.split('/')
            _, type, id = split

            return type, id
    
        raise ValueError('Not a valid Spotify URL')

    def parse_uri(self, uri: str):
        """
        Parses the given URI into a tuple of type and id.

        Args:
            uri: The URI to parse.

        Raises:
            ValueError: If the URI is not a valid Spotify URI.
        """
        split = uri.split(':')
        if len(split) == 3:
            _, type, id = split
            return type, id

        raise ValueError('Not a valid Spotify URI')

    def parse_argument(self, argument: str):
        """
        Parses the given argument into a Spotify ID.
        The main difference between this and [SpotifyClient.parse_url](./client.md#aiospotify.client.SpotifyClient.parse_url)
        or [SpotifyClient.parse_urn](./client.md#aiospotify.client.SpotifyClient.parse_urn) is that
        no matter what you pass in, it will never error, while this could be bad, if the returned value
        is passed in into an API call that expects a Spotify ID it will error.
        """
        try:
            return self.parse_uri(argument)[1]
        except ValueError:
            try:
                return self.parse_url(argument)[1]
            except ValueError:
                return argument

    def get_track(self, uri: str):
        """
        Gets a track from the cache.

        Args:
            uri: The Spotify URL/URI/ID of the track.
        """
        return self._state.get_track(uri)
        
    def get_playlist(self, uri: str):
        """
        Gets a playlist from the cache.

        Args:
            uri: The Spotify URL/URI/ID of the playlist.
        """
        return self._state.get_playlist(uri)

    def get_user(self, uri: str):
        """
        Gets a user from the cache.

        Args:
            uri: The Spotify URL/URI/ID of the user.
        """
        return self._state.get_user(uri)

    def get_artist(self, uri: str):
        """
        Gets an artist from the cache.

        Args:
            uri: The Spotify URL/URI/ID of the artist.
        """
        return self._state.get_artist(uri)

    def get_album(self, uri: str):
        return self._state.get_album(uri)

    def get_show(self, uri: str):
        return self._state.get_show(uri)

    def get_episode(self, uri: str):
        return self._state.get_episode(uri)

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

    async def fetch_tracks(self, uris: List[str], *, market: str=None) -> List[Track]:
        ids = [
            self.parse_argument(uri)
            for uri in uris
        ]

        data = await self.http.get_tracks(
            ids=ids,
            market=market
        )

        return [
            self._state.add_track(Track(item, self._state))
            for item in data['items']
        ]

    async def fetch_track(self, uri: str, *, market: str=None) -> Track:
        id = self.parse_argument(uri)
        data = await self.http.get_track(id, market=market)

        return self._state.add_track(
            track=Track(data, self._state)
        )

    async def fetch_user(self, uri: str):
        id = self.parse_argument(uri)
    
        data = await self.http.get_user(id)
        return self._state.add_user(
            user=User(data)
        )

    async def fetch_playlist(self, uri: str):
        id = self.parse_argument(uri)
        data = await self.http.get_playlist(id)

        return self._state.add_playlist(
            playlist=Playlist(data, self._state)
        )

    async def fetch_shows(self, uris: List[str], *, market: str=None) -> List[Show]:
        ids = [
            self.parse_argument(uri)
            for uri in uris
        ]

        data = await self.http.get_shows(ids, market=market)
        return [
            self._state.add_show(Show(item, self._state))
            for item in data['items']
        ]
    
    async def fetch_show(self, uri: str, *, market: str=None) -> Show:
        id = self.parse_argument(uri)
        data = await self.http.get_show(id, market)

        return self._state.add_show(Show(data, self._state))

    async def close(self):
        await self.http.session.close()