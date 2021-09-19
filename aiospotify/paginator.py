from typing import Any, Callable, Coroutine, Generic, List, TypeVar

T = TypeVar('T')

__all__ = (
    'Paginator',
)

class EmptyPage(Exception):
    pass

class MaxReached(Exception):
    pass

class Paginator(Generic[T]):
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
        callback: Callable[..., Coroutine[Any, Any, List[T]]], 
        increment: int=50,
        max: int=200,
        *args,
        **kwargs,
    ) -> None:
        self.results: List[T] = []
        self.offset = 0
        self.callback = callback
        self.increment = increment
        self.max = max
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return f'<Paginator offset={self.offset} increment={self.increment} max={self.max}>'

    def __len__(self):
        return len(self.results)

    async def all(self) -> List[T]:
        return [*[item async for result in self for item in result]]

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

        self.results.extend(items)
        return items

    def previous(self) -> List[T]:
        self.offset -= self.increment
        return self.results[-self.increment:]

    def __aiter__(self):
        return self

    async def __anext__(self) -> List[T]:
        try:
            return await self.next()
        except (EmptyPage, MaxReached):
            raise StopAsyncIteration