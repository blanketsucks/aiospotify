from enum import Enum

__all__ = (
    'ObjectType',
    'AlbumType'
)

class ObjectType(Enum):
    USER = 'user'
    ALBUM = 'album'
    TRACK = 'track'
    PLAYLIST = 'playlist'
    ARTIST = 'artist'
    GENRE = 'genre'

class AlbumType(Enum):
    ALBUM = 'album'
    SINGLE = 'single'
    COMPOSITION = 'compilation'