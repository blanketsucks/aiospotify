from typing import Any, Dict, Generic, List, Optional, TypeVar, Type

from .http import HTTPClient
from .artist import Artist
from .track import Track
from .utils import cached_slot_property

T = TypeVar('T')

__all__ = 'SearchResult',

class SearchResultItems(Generic[T]):
    __slots__ = (
        'total',
        'limit',
        'offset',
        'next',
        'previous',
        'items'
    )

    def __init__(self, data: Dict[str, Any], http: HTTPClient, type: Type[T]) -> None:    
        self.total: int = data['total']
        self.limit: int = data['limit']
        self.offset: int = data['offset']
        self.next: str = data['next']
        self.previous: Optional[str] = data['previous']

        self.items: List[T] = [type(item, http) for item in data.get('items', [])]

    def __repr__(self) -> str:
        return f'<SearchResultItems total={self.total!r}>'


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

    @cached_slot_property('_cs_artists')
    def artists(self) -> Optional[SearchResultItems[Artist]]:
        data = self._data.get('artists')
        if data is None:
            return None

        return SearchResultItems(data, self._http, Artist)

    @cached_slot_property('_cs_tracks')
    def tracks(self) -> Optional[SearchResultItems[Track]]:
        data = self._data.get('tracks')
        if data is None:
            return None

        return SearchResultItems(data, self._http, Track)