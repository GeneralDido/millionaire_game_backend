# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str  # e.g. "postgresql+asyncpg://user:pass@db:5432/millionaire"
    OPENAI_API_KEY: str
    ADMIN_API_KEY: str
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://millionaire-quiz-frontend.vercel.app",
        "https://peak-puzzler-quiz-frontend-git-main-dimitris-panouris-projects.vercel.app",
        "https://www.peakpuzzler.com",
    ]
    DB_ECHO: bool = False

    # Pydantic v2 way to configure env file
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
