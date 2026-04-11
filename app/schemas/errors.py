from typing import Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status: int
    error: str
    message: str
    field: Optional[str] = None
