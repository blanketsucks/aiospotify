from typing import List, Optional

from .episode import Episode
from .partials import PartialShow, PartialEpisode
from .utils import cached_slot_property

__all__ = ('Show',)

class Show(PartialShow):
    __slots__ = PartialShow.__slots__ + ('_cs_episodes',)

    @cached_slot_property('_cs_episodes')
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