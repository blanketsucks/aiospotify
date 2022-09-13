from typing import Dict, Optional, Protocol, Any

__all__ = (
    'Followers',
    'Copyright',
    'ExternalURLs',
    'ExternalIDs',
    'Object'
)

class Followers:
    def __init__(self, data: Dict[str, Any]):
        self.href: Optional[str] = data.get('href')
        self.total: int = data['total']

class Copyright:
    def __init__(self, data: Dict[str, Any]):
        self.text: str = data['text']
        self.type: str = data['type']

class ExternalURLs:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.spotify: str = data['spotify']

class ExternalIDs:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.ean: str = data['ean']
        self.isrc: str = data['isrc']
        self.upc: str = data['upc']

class Object(Protocol):
    uri: str
    id: str

class IDComparable:
    id: str

    def __eq__(self, other: Any):
        if not isinstance(other, self.__class__):
            return False

        return self.id == other.id
