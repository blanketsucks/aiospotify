from typing import Any, Dict, List
from functools import cached_property

from .state import CacheState
from .partials import PartialArtist
from .track import Track

__all__ = (
    'SearchResult',
)

class SearchResult:
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._data = data
        self._state = state

    def __repr__(self) -> str:
        return f'<SearchResult artists={len(self.arists)} tracks={len(self.tracks)}>'

    @cached_property
    def arists(self) -> List[PartialArtist]:
        artists = self._data.get('artists', {})
        items = artists.get('items', [])

        return [
            self._state.add_artist(PartialArtist(item))
            for item in items
        ]

    @cached_property
    def tracks(self) -> List[Track]:
        tracks = self._data.get('tracks', {})
        items = tracks.get('items', [])

        return [
            self._state.add_track(Track(item, self._state))
            for item in items
        ]
