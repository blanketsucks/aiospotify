from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generic, List, Protocol, TypeVar, Generator
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from typing_extensions import Self

T = TypeVar('T')

M = TypeVar('M')

__all__ = (
    'Paginator',
)

class PaginatorCallback(Protocol, Generic[T]):
    async def __call__(self, *args: Any, offset: int, limit: int) -> List[T]:
        ...

class EmptyPage(Exception):
    pass

class MaxReached(Exception):
    pass

class AbstractPaginator(ABC, Generic[T]):
    items: List[T]

    @abstractmethod
    async def next(self) -> List[T]:
        raise NotImplementedError

    async def all(self) -> List[T]:
        return [item async for item in self]

    def __await__(self) -> Generator[None, None, List[T]]:
        return self.all().__await__()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> T:
        try:
            if self.items:
                return self.items.pop()

            await self.next()
            return self.items.pop()
        except (EmptyPage, MaxReached):
            raise StopAsyncIteration


class Paginator(AbstractPaginator[T]):
    __slots__ = (
        'results', 
        'offset', 
        'callback', 
        'increment',
        'max', 
        'args', 
        'kwargs'
    )

    def __init__(self, 
        callback: PaginatorCallback[T], 
        increment: int = 50,
        max: int = 200,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if 0 > increment <= 100:
            raise ValueError('increment value must be between 1 and 100')

        self.items: List[T] = []
        self.offset = 0
        self.callback = callback
        self.increment = increment
        self.max = max
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return f'<Paginator offset={self.offset} increment={self.increment} max={self.max}>'

    def __len__(self):
        return len(self.items)

    async def next(self) -> List[T]:
        if self.offset >= self.max:
            raise MaxReached

        items = await self.callback(
            *self.args, 
            offset=self.offset, 
            limit=self.increment, 
            **self.kwargs
        )
        if not items:
            raise EmptyPage

        self.offset += self.increment
        self.items.extend(items)

        return items
