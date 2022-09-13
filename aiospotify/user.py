from typing import Any, Dict, List, Optional

from .playback import UserPlayback
from .http import HTTPClient
from .objects import Followers, ExternalURLs
from .image import Image
from .track import UserTrack, Track
from .album import Album
from .partials import PartialUser
from .playlist import Playlist

__all__ = (
    'User',
    'CurrentUser'
)

class User(PartialUser):
    __slots__ = PartialUser.__slots__ + ('_http',)

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._http = http
        super().__init__(data)

    async def create_playlist(
        self, 
        name: str,
        *,
        description: Optional[str] = None,
        public: bool = True,
        collaborative: bool = False
    ) -> Playlist:
        data = await self._http.create_playlist(
            user_id=self.id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description
        )

        return Playlist(data, self._http)

    async def fetch_playlists(self, *, limit: int = 20, offset: int = 0) -> List[Playlist]:
        data = await self._http.get_user_playlists(self.id, limit=limit, offset=offset)
        return [Playlist(item, self._http) for item in data['items']]

    @property
    def external_urls(self):
        return ExternalURLs(self._data.get('external_urls', {}))

    @property
    def images(self) -> List[Image]:
        return [Image(i, self._http) for i in self._data['images']]

    @property
    def followers(self):
        return Followers(self._data['followers'])

class CurrentUser(User):
    __slots__ = User.__slots__ + ('country', 'email', 'product')

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        super().__init__(data, http)

        self.country: Optional[str] = data.get('country')
        self.email: Optional[str] = data.get('email')
        self.product: Optional[str] = data.get('product')

    async def fetch_playback(self) -> UserPlayback:
        data = await self._http.get_user_current_playback()
        return UserPlayback(data, self._http)

    async def fetch_albums(self, *, limit: int = 20, offset: int = 0, market: Optional[str] = None):
        data = await self._http.get_user_saved_albums(limit=limit, offset=offset, market=market)
        return [Album(album, self._http) for album in data['items']]

    async def fetch_saved_tracks(self, *, limit: int = 20, offset: int = 0, market: Optional[str] = None):
        data = await self._http.get_user_saved_tracks(limit=limit, offset=offset, market=market)
        return [UserTrack(track, self._http) for track in data['items']]

    async def fetch_recommendations(self, **kwargs: Any):
        data = await self._http.get_recommendations(**kwargs)
        return [Track(track, self._http) for track in data['tracks']]