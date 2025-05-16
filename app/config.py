# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str  # e.g. "postgresql+asyncpg://user:pass@db:5432/millionaire"
    OPENAI_API_KEY: str

    # Pydantic v2 way to configure env file
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
