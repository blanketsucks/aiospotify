from typing import Any, Dict, List

from .state import CacheState
from .image import Image
from .objects import Followers
from .partials import PartialArtist

__all__ = (
    'Artist'
)

class Artist(PartialArtist):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._state = state
        super().__init__(data)

        self.genres: List[str] = data['genres']
        self.popularity: int = data['popularity']

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    @property
    def followers(self):
        return Followers(
            href=self._data['followers']['href'],
            total=self._data['followers']['total'],
        )
