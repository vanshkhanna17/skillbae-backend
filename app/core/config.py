from enum import Enum
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class SameSiteEnum(str, Enum):
    lax = "lax"
    trict = "strict"
    none = "none"

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


settings = Settings()  # pyright: ignore[reportCallIssue]
