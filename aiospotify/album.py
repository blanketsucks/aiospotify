from typing import Any, Dict, List

from .state import CacheState
from .objects import Copyright, ExternalIDs
from .partials import PartialAlbum, PartialTrack

__all__ = (
    'Album',
)

class Album(PartialAlbum):
    def __init__(self, data: Dict[str, Any], state: CacheState):
        super().__init__(data, state)

        self.popularity: int = data['popularity']

    @property
    def external_ids(self):
        ids = self._data.get('external_ids', {})
        return ExternalIDs(
            ean=ids.get('ean'),
            isrc=ids.get('isrc'),
            upc=ids.get('upc'),
        )

    @property
    def copyrights(self) -> List[Copyright]:
        return [
            Copyright(text=data['text'], type=data['type'])
            for data in self._data['copyrights']
        ]

    def tracks(self) -> List[PartialTrack]:
        tracks = self._data['tracks']['items']
        return [
            self._state.add_track(PartialTrack(data))
            for data in tracks
        ]