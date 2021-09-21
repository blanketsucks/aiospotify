
from typing import Any, Dict, List

from .objects import Followers, ExternalURLs
from .image import Image
from .track import UserTrack, Track
from .state import CacheState
from .album import Album
from .partials import PartialUser
from .playlist import Playlist

__all__ = (
    'User',
    'CurrentUser'
)

class User(PartialUser):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        super().__init__(data)
        self._state = state
        self.display_name: str = data['display_name']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} display_name={self.display_name!r} id={self.id!r} uri={self.uri!r}>'

    async def create_playlist(
        self, 
        name: str,
        *,
        description: str=None,
        public: bool=True,
        collaborative: bool=False
    ):
        data = await self._state.http.create_playlist(
            user_id=self.id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description
        )

        return Playlist(data, self._state)

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