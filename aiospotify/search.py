from typing import Any, Dict, List
from functools import cached_property

from .http import HTTPClient
from .partials import PartialArtist
from .track import Track

__all__ = (
    'SearchResult',
)

class SearchResult:
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._data = data
        self._http = http

    def __repr__(self) -> str:
        return f'<SearchResult artists={len(self.arists)} tracks={len(self.tracks)}>'

    @cached_property
    def arists(self) -> List[PartialArtist]:
        artists = self._data.get('artists', {})
        items = artists.get('items', [])

        return [PartialArtist(artist) for artist in items]

    @cached_property
    def tracks(self) -> List[Track]:
        tracks = self._data.get('tracks', {})
        items = tracks.get('items', [])

        return [Track(track, self._http) for track in items]