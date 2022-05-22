from typing import Any, Dict, BinaryIO, Union
import asyncio
import os

from .http import HTTPClient

__all__ = (
    'Image',
)

async def _write(fd: BinaryIO, data: bytes) -> int:
    return await asyncio.to_thread(fd.write, data)

class Image:
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self.url: str = data['url']
        self.width: int = data.get('width', 0)
        self.height: int = data.get('height', 0)

        self._http = http

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
