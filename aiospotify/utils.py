from __future__ import annotations

from typing import Callable, Generic, Optional, Type, TypeVar, Any, overload
import sys

PY39 = sys.version_info >= (3, 9)

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
