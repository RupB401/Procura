from fastapi import HTTPException
from typing import Any, Dict, Optional

class RFQException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: Optional[str] = None
    ):
        detail = {
            "error": {
                "code": code,
                "message": message,
            }
        }
        if request_id:
            detail["error"]["request_id"] = request_id
            
        super().__init__(status_code=status_code, detail=detail)

class ValidationException(RFQException):
    def __init__(self, message: str = "Request validation failed"):
        super().__init__(status_code=400, code="VALIDATION_ERROR", message=message)

class AuthException(RFQException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(status_code=401, code="AUTHENTICATION_FAILED", message=message)

class ForbiddenException(RFQException):
    def __init__(self, message: str = "Not authorized to access this resource"):
        super().__init__(status_code=403, code="AUTHORIZATION_DENIED", message=message)

class NotFoundException(RFQException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=404, code="RESOURCE_NOT_FOUND", message=message)
        
class StateException(RFQException):
    def __init__(self, message: str = "Invalid state transition"):
        super().__init__(status_code=409, code="STATE_CONFLICT", message=message)
