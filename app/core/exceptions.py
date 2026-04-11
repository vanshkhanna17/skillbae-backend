from typing import Mapping, Optional

from fastapi import HTTPException

from app.schemas.errors import ErrorResponse


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        field: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.error_detail = ErrorResponse(
            status=status_code, error=error, message=message, field=field
        )
        super().__init__(
            status_code, detail=self.error_detail.model_dump(), headers=headers
        )
