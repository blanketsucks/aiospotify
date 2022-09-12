from __future__ import annotations

from typing import Dict, Any, List, Optional

from .http import HTTPClient
from .enums import AlbumType, ObjectType, MediaType
from .image import Image
from .objects import Copyright, ExternalURLs, ExternalIDs, IDComparable
from .utils import cached_slot_property

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
    __slots__ = ('date', 'precision')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.date: str = data['release_date']
        self.precision: str = data['release_date_precision'] 

    def __repr__(self) -> str:
        return '<ReleaseDate date={0.date!r} precision={0.precision!r}>'.format(self)

class PartialEpisode(IDComparable):
    __slots__ = (
        '_data',
        '_http',
        'audio_preview_url',
        'description',
        'duration_ms',
        'href',
        'id',
        'is_externally_hosted',
        'name',
        'language',
        'type',
        'uri'
    )

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._data = data
        self._http = http

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
        return [Image(image, self._http) for image in self._data['images']]

    @property
    def external_urls(self) -> ExternalURLs:
        return ExternalURLs(self._data.get('external_urls', {}))

class PartialShow(IDComparable):
    __slots__ = (
        '_data',
        '_http',
        'available_markets',
        'description',
        'explicit',
        'href',
        'id',
        'is_externally_hosted',
        'languages',
        'name',
        'media_type',
        'type',
        'publisher',
        'uri'
    )

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._data = data
        self._http = http

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
        return [Image(image, self._http) for image in self._data['images']]

    @property
    def copyrights(self) -> List[Copyright]:
        return [Copyright(data) for data in self._data['copyrights']]

    @property
    def external_ids(self) -> ExternalURLs:
        return ExternalURLs(self._data.get('external_urls', {}))
    
class PartialUser(IDComparable):
    __slots__ = ('_data', 'href', 'id', 'type', 'uri', 'display_name')

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self.href: str = data['href']
        self.id: str = data['id']
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']

        # display_name may not exist in some partial payloads
        self.display_name: Optional[str] = data.get('display_name')

    def __repr__(self) -> str:
        if self.display_name is not None:
            return f'<{self.__class__.__name__} id={self.id!r} display_name={self.display_name!r} uri={self.uri}>'
        else:
             return f'<{self.__class__.__name__} id={self.id!r} uri={self.uri}>'

    @property
    def external_urls(self):
        return ExternalURLs(self._data.get('external_urls', {}))

class PartialTrack(IDComparable):
    __slots__ = (
        '_cs_artists'
        '_data',
        'available_markets',
        'disc_number',
        'duration',
        'explicit',
        'href',
        'id',
        'name',
        'preview_url',
        'track_number',
        'type',
        'uri'
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

        self.available_markets: List[str] = data.get('available_markets', [])
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

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} id={self.id!r} uri={self.uri!r}>'
    
    @property
    def external_ids(self):
        return ExternalIDs(self._data.get('external_ids', {}))

    @cached_slot_property('_cs_artists')
    def artists(self) -> List[PartialArtist]:
        artists = self._data.get('artists', [])
        return [PartialArtist(artist) for artist in artists]

class PartialArtist(IDComparable):
    __slots__ = ('_data', 'href', 'id', 'name', 'type', 'uri')

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self.href: str = data['href']
        self.id: str = data['id']
        self.name: str = data['name']
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']

    @property
    def external_urls(self):
        return ExternalURLs(self._data.get('external_urls', {}))

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} id={self.id!r} uri={self.uri!r}>'

class PartialAlbum(IDComparable):
    __slots__ = (
        '_cs_artists',
        '_http',
        '_data',
        'album_type',
        'type',
        'available_markets',
        'href',
        'id',
        'uri',
        'name'
    )

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._http = http
        self._data = data
        self.album_type = AlbumType(data['album_type']) 
        self.type = ObjectType(data['type'])
        self.available_markets: List[str] = data.get('available_markets', [])
        self.href: str = data['href']
        self.id: str = data['id']
        self.uri: str = data['uri']
        self.name: str = data['name']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} uri={self.uri!r}>'

    @property
    def external_urls(self):
        return ExternalURLs(self._data['external_urls'])

    @property
    def release_date(self):
        return ReleaseDate(self._data)

    @property
    def images(self) -> List[Image]:
        return [Image(image, self._http) for image in self._data['images']]

    @cached_slot_property('_cs_artists')
    def artists(self) -> List[PartialArtist]:
        return [PartialArtist(artist) for artist in self._data['artists']]
