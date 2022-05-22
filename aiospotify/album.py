from typing import Any, Dict, List

from .http import HTTPClient
from .objects import Copyright, ExternalIDs
from .partials import PartialAlbum, PartialTrack

__all__ = (
    'Album',
)

class Album(PartialAlbum):
    def __init__(self, data: Dict[str, Any], http: HTTPClient):
        super().__init__(data, http)

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

    @property
    def tracks(self) -> List[PartialTrack]:
        tracks = self._data.get('tracks', {})
        items = tracks.get('items', [])

        return [PartialTrack(track) for track in items]