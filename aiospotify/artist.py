from typing import Any, Dict, List

from .state import CacheState
from .image import Image
from .objects import Followers
from .partials import PartialArtist
from .track import Track

__all__ = (
    'Artist',
)

class Artist(PartialArtist):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._state = state
        super().__init__(data)

        self.genres: List[str] = data['genres']
        self.popularity: int = data['popularity']

    async def fetch_top_tracks(self, *, market: str=None) -> List[Track]:
        data = await self._state.http.get_artist_top_tracks(
            id=self.id,
            market=market
        )

        return [
            self._state.add_track(Track(track, self._state))
            for track in data['tracks']
        ]

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    @property
    def followers(self):
        return Followers(
            href=self._data['followers']['href'],
            total=self._data['followers']['total'],
        )
