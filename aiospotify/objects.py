from typing import Union, NamedTuple, Optional

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

class Object:
    def __init__(self, id: str, type: str) -> None:
        self.id = id
        self.uri = f'spotify:{type}:{id}'