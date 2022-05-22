from typing import List, Dict, Any, Optional

from .http import HTTPClient
from .episode import Episode
from .partials import PartialShow, PartialEpisode

__all__ = ('Show',)

class Show(PartialShow):
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        super().__init__(data, http)

    @property
    def episodes(self) -> List[PartialEpisode]:
        return [PartialEpisode(item, self._http) for item in self._data['episodes']['items']]

    async def fetch_episodes(
        self, 
        *, 
        market: Optional[str] = None, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Episode]:
        data = await self._http.get_show_episodes(
            id=self.id,
            market=market,
            limit=limit,
            offset=offset
        )

        return [Episode(item, self._http) for item in data['items']]