from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


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


settings = Settings()  # pyright: ignore[reportCallIssue]
