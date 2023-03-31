from __future__ import annotations

from typing import Callable, Generic, Optional, Type, TypeVar, Any, overload, Tuple
import datetime
import sys
import re

PY39 = sys.version_info >= (3, 9)
PY310 = sys.version_info >= (3, 10)

SPOTIFY_URL_REGEX = re.compile(r'https:\/\/(open.spotify.com|play.spotify.com)\/(?P<type>user|track|album|artist|playlist|show)\/(?P<id>\w*)')
SPOTIFY_URI_REGEX = re.compile(r'^spotify:(?P<type>user|track|album|artist|playlist|show):(?P<id>.*)$')

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)

class CachedSlotProperty(Generic[T, T_co]):
    def __init__(self, name: str, func: Callable[[T], T_co]) -> None:
        self.name = name
        self.func = func
        self.__doc__ = getattr(func, '__doc__')

    @overload
    def __get__(self, instance: None, owner: Type[T]) -> CachedSlotProperty[T, T_co]:
        ...
    @overload
    def __get__(self, instance: T, owner: Type[T]) -> T_co:
        ...
    def __get__(self, instance: Optional[T], owner: Type[T]) -> Any:
        if instance is None:
            return self

        try:
            value = getattr(instance, self.name)
        except AttributeError:
            value = self.func(instance)
            setattr(instance, self.name, value)

        return value

def cached_slot_property(name: str) -> Callable[[Callable[[T], T_co]], CachedSlotProperty[T, T_co]]:
    def decorator(func: Callable[[T], T_co]) -> CachedSlotProperty[T, T_co]:
        return CachedSlotProperty(name, func)
    return decorator

def fromisoformat(date: str) -> datetime.datetime:
    if date.endswith('Z'):
        date = date[:-1]

    return datetime.datetime.fromisoformat(date)

def _parse_from_regex(regex: re.Pattern, string: str) -> Tuple[str, str]:
    match = regex.match(string)
    if not match:
        raise ValueError(f'{string!r} is not a valid spotify url or uri')

    return match.group('type'), match.group('id')

def parse_uri(uri: str) -> Tuple[str, str]:
    return _parse_from_regex(SPOTIFY_URI_REGEX, uri)

def parse_url(url: str) -> Tuple[str, str]:
    return _parse_from_regex(SPOTIFY_URL_REGEX, url)

def parse_argument(argument: str, type: str) -> str:
    try:
        typ, id = parse_uri(argument)
    except ValueError:
        try:
            typ, id = parse_url(argument)
        except ValueError:
            return argument # Assume the argument is a raw id

    if type != typ:
        raise ValueError(f'{argument!r} is not a valid {type} url or uri')

    return id