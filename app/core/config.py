from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class SameSiteEnum(str, Enum):
    lax = "lax"
    strict = "strict"
    none = "none"

    @classmethod
    def _missing_(cls, value: Any):
        """Normalize case-insensitive env values."""
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str
    app_description: str
    app_version: str
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
    backend_cors_origins: str = Field(
        default=""
    )  # 👈 str, not list — avoids JSON decode
    cookie_domain: str | None = None
    debug: bool
    redis_url: str

    @model_validator(mode="after")
    def parse_list_fields(self) -> "Settings":
        value = self.backend_cors_origins
        if not value or value.strip() == "":
            object.__setattr__(self, "backend_cors_origins", [])
        else:
            origins = [o.strip() for o in value.split(",") if o.strip()]
            object.__setattr__(self, "backend_cors_origins", origins)
        return self

    @field_validator("cookie_domain", mode="before")
    @classmethod
    def normalize_cookie_domain(cls, value: Any) -> str | None:
        if not value or str(value).lower() == "none":
            return None
        return value


settings = Settings()  # pyright: ignore[reportCallIssue]
