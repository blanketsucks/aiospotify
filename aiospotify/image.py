from __future__ import annotations

from typing import Any, Dict, BinaryIO, Union
import asyncio
import os

from .http import HTTPClient
from .utils import PY39

__all__ = (
    'Image',
)

async def _write(fd: BinaryIO, data: bytes) -> int:
    if PY39:
        return await asyncio.to_thread(fd.write, data)
    else:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, fd.write, data)

class Image:
    __slots__ = ('_http', 'url', 'width', 'height')

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._http = http

        self.url: str = data['url']
        self.width: int = data.get('width', 0)
        self.height: int = data.get('height', 0)

    def __repr__(self) -> str:
        return f'<Image url={self.url!r}>'
    
    def __str__(self) -> str:
        return self.url

    async def read(self) -> bytes:
        return await self._http.read(self.url)

    async def save(self, file: Union[str, os.PathLike[str], BinaryIO]) -> int:
        data = await self.read()
        if isinstance(file, (str, os.PathLike)):
            with open(file, 'wb') as f:
                return await _write(f, data)
        
        return await _write(file, data)
