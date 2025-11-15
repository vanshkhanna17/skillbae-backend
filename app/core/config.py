from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str 
    app_description: str
    app_version: str 
    debug: bool
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()
