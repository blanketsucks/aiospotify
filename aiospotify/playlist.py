from __future__ import annotations

from typing import Dict, Any, List, Optional, Sequence

from .http import HTTPClient
from .image import Image
from .objects import Followers, ExternalURLs
from .track import Track
from .objects import Object
from .partials import PartialUser
from .paginator import Paginator

__all__ = ('PlaylistTrack', 'Playlist')

class PlaylistTrack(Track):
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        super().__init__(data['track'], http)
        self.added_at = data['added_at']
        self.added_by = PartialUser(data['added_by'])
        self.is_local: bool = data['is_local']

class PlaylistTracks:
    def __init__(self, playlist: Playlist, data: Dict[str, Any]) -> None:
        self.playlist = playlist
        self.href: str = data['href']
        self.total: int = data['total']

    def __repr__(self) -> str:
        return f'<PlaylistTracks href={self.href!r} total={self.total!r}>'

    def fetch(self, **kwargs: Any) -> Paginator[PlaylistTrack]:
        return Paginator(self.playlist.read, max=self.total, **kwargs)

class Playlist:
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._data = data
        self._http = http

        self.collaborative: bool = data['collaborative']
        self.description: str = data['description']
        self.href: str = data['href']
        self.id: str = data['id']
        self.name: str = data['name']
        self.public: bool = data['public']
        self.snapshot_id: str = data['snapshot_id']

    def __repr__(self) -> str:
        return f'<Playlist id={self.id!r} name={self.name!r} public={self.public}>'

    async def read(
        self, 
        *, 
        limit: int = 20, 
        offset: int = 0, 
        market: Optional[str] = None, 
        fields: Optional[List[str]] = None, 
        additional_types: Optional[List[str]] = None,
    ) -> List[PlaylistTrack]:
        data = await self._http.get_playlist_items(
            id=self.id,
            limit=limit,
            offset=offset,
            market=market,
            fields=fields,
            additional_types=additional_types
        )

        return [PlaylistTrack(track, self._http) for track in data['items']]

    async def edit(
        self, 
        *, 
        name: Optional[str] = None, 
        description: Optional[str] = None, 
        public: Optional[bool] = None, 
        collaborative: Optional[bool] = None
    ) -> None:
        await self._http.change_playlist_details(
            id=self.id,
            name=name,
            description=description,
            public=public,
            collaborative=collaborative
        )

    async def add_items(
        self,
        items: Optional[Sequence[Object]] = None,
        *,
        position: Optional[int] = None,
    ) -> None:
        items = items or []
        uris = [item.uri for item in items]

        await self._http.add_items_to_playlist(id=self.id, uris=uris, position=position)

    async def remove_tracks(self, tracks: Optional[Sequence[Object]] = None) -> None:
        tracks = tracks or []
        items = [{'uri': track.uri} for track in tracks]

        await self._http.remove_items_from_playlist(id=self.id, tracks=items)

    @property
    def external_urls(self):
        return ExternalURLs(self._data.get('external_urls', {}))

    @property
    def owner(self) -> PartialUser:
        return PartialUser(self._data['owner'])

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._http) for image in self._data['images']]

    @property
    def followers(self):
        return Followers(self._data['followers'])

    @property
    def tracks(self):
        return PlaylistTracks(self, self._data['tracks'])
