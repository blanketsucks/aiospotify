from typing import Dict, Any, List, Optional
import datetime

from .image import Image
from .objects import Followers, ExternalURLs
from .user import User
from .track import Track
from .state import CacheState

__all__ = ('PlaylistTrack', 'Playlist')

class PlaylistTrack(Track):
    def __init__(self, data: Dict[str, Any], state: CacheState, playlist: 'Playlist') -> None:
        super().__init__(data['track'], state)
        self.playlist = playlist
        self.added_at = datetime.datetime.fromisoformat(data['added_at'])
        self.added_by = User(data['added_by'])
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

    @property
    def external_urls(self):
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)

    @property
    def owner(self) -> User:
        return User(self._data['owner'])

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
        if (track := self._state.get_track(uri)) is not None:
            if getattr(track, 'playlist', None) == self:
                return track

            return None

        if (track := self._state.get_track_from_uri(uri)) is not None:
            if getattr(track, 'playlist', None) == self:
                return track

            return None