from typing import Dict, Any, List, Optional, Union

from .image import Image
from .objects import Followers, ExternalURLs
from .track import Track
from .state import CacheState
from .objects import Object
from .partials import PartialTrack, PartialUser

__all__ = ('PlaylistTrack', 'Playlist')

class PlaylistTrack(Track):
    def __init__(self, data: Dict[str, Any], state: CacheState, playlist: 'Playlist') -> None:
        super().__init__(data['track'], state)
        self.playlist = playlist
        self.added_at = data['added_at']
        self.added_by = PartialUser(data['added_by'])
        self.is_local: bool = data['is_local']

class Playlist:
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._data = data
        self._state = state

        self.collaborative: bool = data['collaborative']
        self.description: str = data['description']
        self.href: str = data['href']
        self.id: str = data['id']
        self.name: str = data['name']
        self.public: bool = data['public']
        self.snapshot_id: str = data['snapshot_id']

    async def update(self, *args):
        data = await self._state.http.get_playlist(self.id, *args)
        self.__init__(data, self._state)

        return self

    async def read(
        self, 
        *, 
        limit: int=20, 
        offset: int=0, 
        market: str=None, 
        fields: List[str]=None, 
        additional_types: List[str]=None
    ) -> List[PlaylistTrack]:
        data = await self._state.http.get_playlist_items(
            id=self.id,
            limit=limit,
            offset=offset,
            market=market,
            fields=fields,
            additional_types=additional_types
        )

        return [
            self._state.add_track(PlaylistTrack(track, self._state.http, self))
            for track in data['items']
        ]

    async def edit(
        self, 
        *, 
        name: str=None, 
        description: str=None, 
        public: bool=None, 
        collaborative: bool=None
    ):
        await self._state.http.change_playlist_details(
            id=self.id,
            name=name,
            description=description,
            public=public,
            collaborative=collaborative
        )

    async def add_items(
        self,
        items: List[Union[Object, Track, PartialTrack]]=None,
        position: int=None,
    ):
        items = items or []
        uris = [item.uri for item in items]

        await self._state.http.add_items_to_playlist(
            id=self.id,
            uris=uris,
            position=position
        )

    async def delete_tracks(self, tracks: List[Union[Object, Track, PartialTrack]]=None):
        tracks = tracks or []
        items = {
            'tracks': [
                {'uri': track.uri} for track in tracks
            ]
        }

        await self._state.http.remove_items_from_playlist(
            id=self.id,
            tracks=items
        )


    @property
    def external_urls(self):
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)

    @property
    def owner(self) -> PartialUser:
        return PartialUser(self._data['owner'])

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    @property
    def followers(self):
        return Followers(
            href=self._data['followers']['href'],
            total=self._data['followers']['total'],
        )

    def tracks(self) -> List[PlaylistTrack]:
        tracks = self._data['tracks']['items']
        return [
            self._state.add_track(PlaylistTrack(track, self._state.http, self)) 
            for track in tracks
        ]

    def get_track(self, uri: str) -> Optional[PlaylistTrack]:
        track = self._state.get_track(uri)
        if getattr(track, 'playlist', None):
            return track

        return None