from typing import Dict, Any, List

from .enums import AlbumType, ObjectType
from .image import Image
from .state import CacheState
from .objects import ExternalURLs, ExternalIDs

__all__ = (
    'PartialTrack',
    'PartialAlbum',
    'PartialArtist',
    'AlbumReleaseDate'
)

class PartialTrack:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

        self.avaliable_markets: List[str] = data['available_markets']
        self.disc_number: int = data['disc_number']
        self.duration: int = data['duration_ms']
        self.explicit: bool = data['explicit']
        self.href: str = data['href']
        self.id: str = data['id']
        self.name: str = data['name']
        self.preview_url: str = data['preview_url']
        self.track_number: int = data['track_number']
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']
    
    @property
    def external_ids(self):
        ids = self._data.get('external_ids', {})
        return ExternalIDs(
            ean=ids.get('ean'),
            isrc=ids.get('isrc'),
            upc=ids.get('upc'),
        )

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} id={self.id!r} uri={self.uri!r}>'

    def artists(self) -> List['PartialArtist']:
        artists = self._data.get('artists', [])
        return [PartialArtist(artist) for artist in artists]

class PartialArtist:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self.href: str = data['href']
        self.id: str = data['id']
        self.name: str = data['name']
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']

    @property
    def external_urls(self):
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} id={self.id!r} uri={self.uri!r}>'

class AlbumReleaseDate:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.date: str = data['release_date']
        self.precision: str = data['release_date_precision'] 

class PartialAlbum:
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._state = state
        self._data = data
        self.album_type = AlbumType(data['album_type']) 
        self.type = ObjectType(data['type'])
        self.available_markets: List[str] = data['available_markets']
        self.href: str = data['href']
        self.id: str = data['id']
        self.uri: str = data['uri']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} uri={self.uri!r}>'

    @property
    def external_urls(self):
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)

    @property
    def release_date(self):
        return AlbumReleaseDate(self._data)

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    def artists(self) -> List[PartialArtist]:
        data = self._data['artists']
        return [
            self._state.add_artist(PartialArtist(artist))
            for artist in data
        ]

    
