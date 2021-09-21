from typing import Dict, Any, List

from .enums import AlbumType, ObjectType, MediaType
from .image import Image
from .state import CacheState
from .objects import Copyright, ExternalURLs, ExternalIDs

__all__ = (
    'PartialTrack',
    'PartialUser',
    'PartialEpisode',
    'PartialShow',
    'PartialAlbum',
    'PartialArtist',
    'ReleaseDate'
)

class ReleaseDate:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.date: str = data['release_date']
        self.precision: str = data['release_date_precision'] 

    def __repr__(self) -> str:
        return '<ReleaseDate date={0.date!r} precision={0.precision!r}>'.format(self)

class PartialEpisode:
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._data = data
        self._state = state

        self.audio_preview_url: str = data['audio_preview_url']
        self.description: str = data['description']
        self.duration_ms: int = data['duration_ms']
        self.href: str = data['href']
        self.id: str = data['id']
        self.is_externally_hosted: bool = data['is_externally_hosted']
        self.name: str = data['name']
        self.language: str = data['language']
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} id={self.id!r} uri={self.uri!r}>'

    @property
    def release_date(self):
        return ReleaseDate(self._data)

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    @property
    def external_urls(self) -> ExternalURLs:
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)

class PartialShow:
    def __init__(self, data: Dict[str, Any], state: CacheState) -> None:
        self._data = data
        self._state = state

        self.available_markets: List[str] = data['available_markets']
        self.description: str = data['description']
        self.explicit: bool = data['explicit']
        self.href: str = data['href']
        self.id: str = data['id']
        self.is_externally_hosted: bool = data['is_externally_hosted']
        self.languages: List[str] = data['languages']
        self.name: str = data['name']
        self.media_type = MediaType(data['media_type'])
        self.type = ObjectType(data['type'])
        self.publisher: str = data['publisher']
        self.uri: str = data['uri']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} id={self.id!r} uri={self.uri!r}>'
    
    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    @property
    def copyrights(self) -> List[Copyright]:
        return [
            Copyright(text=data['text'], type=data['type'])
            for data in self._data['copyrights']
        ]

    @property
    def external_ids(self) -> ExternalIDs:
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)
    
class PartialUser:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self.href: str = data['href']
        self.id: str = data['id']
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']

    @property
    def external_urls(self):
        spotify = self._data.get('external_urls', {}).get('spotify', None)
        return ExternalURLs(spotify)

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
        return ReleaseDate(self._data)

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._state.http) for image in self._data['images']]

    def artists(self) -> List[PartialArtist]:
        data = self._data['artists']
        return [
            self._state.add_artist(PartialArtist(artist))
            for artist in data
        ]

    
