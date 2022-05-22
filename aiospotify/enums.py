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

class DeviceType(Enum):
    COMPUTER = 'computer'
    SMARTPHONE = 'smartphone'
    SPEAKER = 'speaker'

class CurrentPlayingType(Enum):
    TRACK = 'track'
    AD = 'ad'
    EPISODE = 'episode'
    UNKNOWN = 'unknown'

class RepeatState(Enum):
    OFF = 'off'
    TRACK = 'track'
    CONTEXT = 'context'

class ShuffleState(Enum):
    OFF = 'off'
    ON = 'on'
