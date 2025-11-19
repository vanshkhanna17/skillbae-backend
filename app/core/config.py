from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = Field(alias="APP_NAME")
    app_description: str = Field(alias="APP_DESCRIPTION")
    app_version: str = Field(alias="APP_VERSION")
    debug: bool = Field(alias="DEBUG")
    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")


settings = Settings()  # pyright: ignore[reportCallIssue]
