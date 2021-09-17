from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Union, Optional


if TYPE_CHECKING:
    from .partials import (
        PartialAlbum,
        PartialArtist,
        PartialTrack,
    )
    from .user import User
    from .track import Track
    from .album import Album
    from .artist import Artist
    from .playlist import Playlist, PlaylistTrack

    from .client import SpotifyClient

class CacheState:
    def __init__(self, client: SpotifyClient) -> None:
        self.client = client
        self.http = client.http

        self._tracks: Dict[str, Union[PartialTrack, Track, PlaylistTrack]] = {}
        self._albums: Dict[str, Union[PartialAlbum, Album]] = {}
        self._artists: Dict[str, Union[PartialArtist, Artist]] = {}
        self._playlists: Dict[str, Playlist] = {}
        self._users: Dict[str, User] = {}

    def get_track(self, track_id: str) -> Optional[Union[PartialTrack, Track, PlaylistTrack]]:
        return self._tracks.get(track_id)

    def get_album(self, album_id: str) -> Optional[Union[PartialAlbum, Album]]:
        return self._albums.get(album_id)

    def get_artist(self, artist_id: str) -> Optional[Union[PartialArtist, Artist]]:
        return self._artists.get(artist_id)

    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        return self._playlists.get(playlist_id)

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_playlist_from_uri(self, uri: str):
        id = self.client.verify_argument(uri, 'playlist')
        return self.get_playlist(id)

    def get_track_from_uri(self, uri: str):
        id = self.client.verify_argument(uri, 'track')
        return self.get_track(id)

    def get_album_from_uri(self, uri: str):
        id = self.client.verify_argument(uri, 'album')
        return self.get_album(id)
    
    def get_user_from_uri(self, uri: str):
        id = self.client.verify_argument(uri, 'user')
        return self.get_user(id)

    def add_track(self, track: Union[PartialTrack, Track, PlaylistTrack]):
        self._tracks[track.id] = track
        return track

    def add_album(self, album: Union[PartialAlbum, Album]):
        self._albums[album.id] = album
        return album

    def add_artist(self, artist: Union[PartialArtist, Artist]):
        self._artists[artist.id] = artist
        return artist

    def add_playlist(self, playlist: Playlist):
        self._playlists[playlist.id] = playlist
        return playlist

    def add_user(self, user: User):
        self._users[user.id] = user
        return user
