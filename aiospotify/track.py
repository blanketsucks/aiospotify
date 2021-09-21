from typing import Dict, Any

from .partials import PartialTrack, PartialAlbum
from .state import CacheState

__all__ = ('Track', 'UserTrack')

class Track(PartialTrack):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._state = state
        super().__init__(data)
    
        self.is_playable = data.get('is_playable', False)
        self.linked_from = PartialTrack(data['linked_from']) if data.get('linked_from') else None

    def album(self) -> PartialAlbum:
        album = self._data['album']
        return self._state.add_album(
            album=PartialAlbum(album, self._state)
        )

    async def fetch_audio_features(self):
        return await self._state.http.get_track_audio_features(self.id)

class UserTrack(Track):
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        super().__init__(data['track'], state)
        self.added_at = data['added_at']
