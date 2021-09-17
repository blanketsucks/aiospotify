from typing import Any, Dict

__all__ = (
    'SpotifyException',
    'HTTPException',
    'Forbidden',
    'BadRequest',
    'NotFound',
    'Unauthorized'
)

class SpotifyException(Exception):
    pass

class HTTPException(SpotifyException):
    def __init__(self, data: Dict[str, Any]) -> None:
        self.error: Dict[str, Any] = data['error']
        self.message: str = self.error['message']
        self.status: int = self.error['status']

        super().__init__(self.message)

class Forbidden(HTTPException):
    pass

class BadRequest(HTTPException):
    pass

class NotFound(HTTPException):
    pass    

class Unauthorized(HTTPException):
    pass
        