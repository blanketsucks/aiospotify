from enum import Enum

__all__ = (
    'ObjectType',
    'AlbumType',
    'MediaType'
)

class ObjectType(Enum):
    USER = 'user'
    ALBUM = 'album'
    TRACK = 'track'
    PLAYLIST = 'playlist'
    ARTIST = 'artist'
    EPISODE = 'episode'
    SHOW = 'show'

class AlbumType(Enum):
    ALBUM = 'album'
    SINGLE = 'single'
    COMPOSITION = 'compilation'

class MediaType(Enum):
    AUDIO = 'audio'
