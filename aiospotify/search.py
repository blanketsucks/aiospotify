from typing import Any, Dict, List

from .http import HTTPClient
from .artist import Artist
from .track import Track
from .utils import cached_slot_property

__all__ = (
    'SearchResult',
)

class SearchResult:
    __slots__ = (
        '_cs_artists',
        '_cs_tracks',
        '_data',
        '_http'
    )

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._data = data
        self._http = http

    def __repr__(self) -> str:
        return f'<SearchResult artists={len(self.arists)} tracks={len(self.tracks)}>'

    @cached_slot_property('_cs_artists')
    def arists(self) -> List[Artist]:
        artists = self._data.get('artists', {})
        items = artists.get('items', [])

        return [Artist(artist, self._http) for artist in items]

    @cached_slot_property('_cs_tracks')
    def tracks(self) -> List[Track]:
        tracks = self._data.get('tracks', {})
        items = tracks.get('items', [])

        return [Track(track, self._http) for track in items]