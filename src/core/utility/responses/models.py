from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime

class SuccessResponse(BaseModel):
    """Base model for every response from the API"""
    message: str = "success"
    data: Optional[Any] = None
    timestamp: Optional[datetime] = datetime.now()
    status_code: int

class ErrorResponse(BaseModel):
    """Base model for every error response from the API"""
    message: str = "error"
    errors: List[str] = []
    line: int
    file: str
    timestamp: Optional[datetime] = datetime.now()
    status_code: int
