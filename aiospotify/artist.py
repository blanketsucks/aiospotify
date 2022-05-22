from __future__ import annotations

from typing import Any, Dict, List, Optional

from .http import HTTPClient
from .image import Image
from .objects import Followers
from .partials import PartialArtist
from .track import Track

__all__ = (
    'Artist',
)

class Artist(PartialArtist):
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._http = http
        super().__init__(data)

        self.genres: List[str] = data['genres']
        self.popularity: int = data['popularity']

    async def fetch_top_tracks(self, *, market: Optional[str] = None) -> List[Track]:
        data = await self._http.get_artist_top_tracks(id=self.id, market=market)
        return [Track(track, self._http) for track in data['tracks']]

    async def fetch_related_artists(self) -> List[Artist]:
        data = await self._http.get_artist_related_artists(self.id)
        return [Artist(artist, self._http) for artist in data['artists']]

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._http) for image in self._data['images']]

    @property
    def followers(self):
        return Followers(
            href=self._data['followers']['href'],
            total=self._data['followers']['total'],
        )
