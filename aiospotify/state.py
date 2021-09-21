from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Union, Optional


if TYPE_CHECKING:
    from .partials import (
        PartialAlbum,
        PartialArtist,
        PartialTrack,
        PartialShow,
        PartialEpisode
    )
    from .user import User
    from .track import Track
    from .album import Album
    from .artist import Artist
    from .playlist import Playlist, PlaylistTrack
    from .show import Show
    from .episode import Episode

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
        self._shows: Dict[str, Union[PartialShow, Show]] = {}
        self._episodes: Dict[str, Union[PartialEpisode, Episode]] = {}

    def get_track(self, uri: str) -> Optional[Union[PartialTrack, Track, PlaylistTrack]]:
        id = self.client.parse_argument(uri)
        return self._tracks.get(id)

    def get_album(self, uri: str) -> Optional[Union[PartialAlbum, Album]]:
        id = self.client.parse_argument(uri)
        return self._albums.get(id)

    def get_artist(self, uri: str) -> Optional[Union[PartialArtist, Artist]]:
        id = self.client.parse_argument(uri)
        return self._artists.get(id)

    def get_playlist(self, uri: str) -> Optional[Playlist]:
        id = self.client.parse_argument(uri)
        return self._playlists.get(id)

    def get_user(self, uri: str) -> Optional[User]:
        id = self.client.parse_argument(uri)
        return self._users.get(id)

    def get_show(self, uri: str) -> Optional[Union[PartialShow, Show]]:
        id = self.client.parse_argument(uri)
        return self._shows.get(id)
    
    def get_episode(self, uri: str) -> Optional[Union[PartialEpisode, Episode]]:
        id = self.client.parse_argument(uri)
        return self._episodes.get(id)

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
        self._playlists[playlist.snapshot_id] = playlist
        return playlist

    def add_user(self, user: User):
        self._users[user.id] = user
        return user

    def add_show(self, show: Union[PartialShow, Show]):
        self._shows[show.id] = show
        return show

    def add_episode(self, episode: Union[PartialEpisode, Episode]):
        self._episodes[episode.id] = episode
        return episode
