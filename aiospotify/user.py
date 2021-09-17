
from typing import Any, Dict, List

from .objects import Followers, ExternalURLs
from .image import Image
from .enums import ObjectType
from .track import UserTrack, Track
from .state import CacheState
from .album import Album

__all__ = (
    'User',
    'CurrentUser'
)

class User:
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._data = data
        self._state = state
        self.href: str = data['href']
        self.id: str = data['id']
        self.type = ObjectType(data['type'])
        self.display_name: str = data['display_name']
        self.uri: str = data['uri']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} display_name={self.display_name!r} id={self.id!r} uri={self.uri!r}>'

    @property
    def external_urls(self):
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)
    
    @property
    def images(self) -> List[Image]:
        return [Image(i, self._state.http) for i in self._data['images']]

    @property
    def followers(self):
        return Followers(
            href=self._data['followers']['href'],
            total=self._data['followers']['total'],
        )

class CurrentUser(User):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        super().__init__(data, state)

        self.country: str = data.get('country', '')
        self.email: str = data.get('email', '')
        self.product: str = data.get('product', '')

    async def fetch_current_playback(self, *, market: str=None, additional_types: List[str]=None):
        playback = await self._state.http.get_user_current_playback(
            market=market,
            additional_types=additional_types,
        )

    async def fetch_albums(self, *, limit: int=20, offset: int=0, market: str=None):
        albums = await self._state.http.get_user_saved_albums(
            limit=limit,
            offset=offset,
            market=market
        )

        return [
            self._state.add_album(Album(a, self._state))
            for a in albums['items']
        ]

    async def fetch_tracks(self, *, limit: int=20, offset: int=0, market: str=None):
        tracks = await self._state.http.get_user_saved_tracks(
            limit=limit,
            offset=offset,
            market=market,
        )

        return [UserTrack(t, self._state) for t in tracks['items']]

    async def fetch_recommendations(self, **kwargs):
        recommendations = await self._state.http.get_recommendations(**kwargs)
        return [Track(t, self._state) for t in recommendations['tracks']]