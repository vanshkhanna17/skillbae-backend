from enum import Enum
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class SameSiteEnum(str, Enum):
    lax = "Lax"
    strict = "Strict"
    none = "None"

    @classmethod
    def _missing_(cls, value: Any):
        """Normalize case-insensitive env values."""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str
    app_description: str
    app_version: str
    debug: bool
    database_url: str
    database_sync_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_secret_key: str
    refresh_token_expire_days: int
    cookie_secure: bool
    cookie_samesite: SameSiteEnum = Field(default=SameSiteEnum.lax)
    cookie_path: str
    backend_cors_origins: str
    cookie_domain: str

    # FIX: Convert comma-separated string into Python list
    @field_validator("backend_cors_origins", mode="after")
    def convert_cors_to_list(cls, value: Any):
        if not value:
            return []
        return [origin.strip() for origin in value.split(",") if origin.strip()]


settings = Settings()  # pyright: ignore[reportCallIssue]
