from typing import Any, Dict

from .http import HTTPClient

__all__ = (
    'Image',
)

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
