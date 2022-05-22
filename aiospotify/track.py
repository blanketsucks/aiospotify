from typing import Dict, Any

from .partials import PartialTrack, PartialAlbum
from .http import HTTPClient

__all__ = ('Track', 'UserTrack')

class Track(PartialTrack):
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._http = http
        super().__init__(data)
    
        self.is_playable = data.get('is_playable', False)
        self.linked_from = PartialTrack(data['linked_from']) if data.get('linked_from') else None

    @property
    def album(self) -> PartialAlbum:
        return PartialAlbum(self._data['album'], self._http)

    async def fetch_audio_features(self):
        return await self._http.get_track_audio_features(self.id)

class UserTrack(Track):
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        super().__init__(data['track'], http)
        self.added_at = data['added_at']
