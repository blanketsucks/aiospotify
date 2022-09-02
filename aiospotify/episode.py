from typing import Dict, Any, List

from .http import HTTPClient
from .partials import PartialEpisode, PartialShow

class Episode(PartialEpisode):
    __slots__ = PartialEpisode.__slots__ + ('is_playable', 'languages')

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        super().__init__(data, http)

        self.is_playable: bool = data['is_playable']
        self.languages: List[str] = data['languages']

    @property
    def show(self) -> PartialShow:
        return PartialShow(self._data['show'], self._http)