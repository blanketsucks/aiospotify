from enum import Enum

__all__ = (
    'ObjectType',
    'AlbumType',
    'MediaType'
)

class ObjectType(Enum):
    User = 'user'
    Album = 'album'
    Track = 'track'
    Playlist = 'playlist'
    Artist = 'artist'
    Episode = 'episode'
    SHOW = 'show'

class AlbumType(Enum):
    Album = 'album'
    Single = 'single'
    Compilation = 'compilation'

class MediaType(Enum):
    Audio = 'audio'

class DeviceType(Enum):
    Computer = 'computer'
    Smartphone = 'smartphone'
    Speaker = 'speaker'

class CurrentPlayingType(Enum):
    Track = 'track'
    Ad = 'ad'
    Episode = 'episode'
    Unknown = 'unknown'

class RepeatState(Enum):
    Off = 'off'
    Track = 'track'
    Context = 'context'

class ShuffleState(Enum):
    Off = 'off'
    On = 'on'
