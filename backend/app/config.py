"""
app/config.py — centralised settings loaded from .env
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # AI
    google_api_key: str = ""
    openai_api_key: str = ""
    ai_provider: str = "gemini"

    # App
    app_env: str = "development"
    secret_key: str = "changeme"

    # DB
    database_url: str = "sqlite+aiosqlite:///./data/analyst.db"

    # Upload
    max_upload_size_mb: int = 50
    upload_dir: str = "./uploads"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
