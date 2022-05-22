from typing import NamedTuple, Optional, Protocol

__all__ = (
    'Followers',
    'Copyright',
    'ExternalURLs',
    'ExternalIDs',
    'Object'
)

class Followers(NamedTuple):
    href: Optional[str]
    total: int

class Copyright(NamedTuple):
    text: str
    type: str

class ExternalURLs(NamedTuple):
    spotify: str

class ExternalIDs(NamedTuple):
    ean: str
    isrc: str
    upc: str

class Object(Protocol):
    uri: str