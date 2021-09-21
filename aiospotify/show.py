from typing import List, Dict, Any

from .state import CacheState
from .episode import Episode
from .partials import PartialShow, PartialEpisode

class Show(PartialShow):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        super().__init__(data, state)

        self.episodes: List[PartialEpisode] = [
            PartialEpisode(episode, state)
            for episode in data['episodes']['items']
        ]

    async def fetch_episodes(self, *, market: str=None, limit: int=20, offset: int=0) -> List[Episode]:
        data = await self._state.http.get_show_episodes(
            id=self.id,
            market=market,
            limit=limit,
            offset=offset
        )

        return [
            self._state.add_episode(Episode(item, self._state))
            for item in data['items']
        ]