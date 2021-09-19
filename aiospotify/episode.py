from typing import Dict, Any, List

from .state import CacheState
from .partials import PartialEpisode, PartialShow

class Episode(PartialEpisode):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        super().__init__(data, state)

        self.is_playable: bool = data['is_playable']
        self.languages: List[str] = data['languages']

    @property
    def show(self) -> PartialShow:
        return PartialShow(
            self._data['show'],
            self._state
        )