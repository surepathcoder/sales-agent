"""
Application settings loaded from environment variables.

Uses pydantic-settings for validation and type coercion.
All secrets must come from env — never hardcode in source.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Kijani AI"
    app_env: Literal["development", "staging", "production"] = "development"
    app_frontend_url: str = "http://localhost:3000"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://kijani:kijani_dev_pass@localhost:5433/kijani"
    )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # JWT
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars!!",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    refresh_token_expire_minutes: int = 10080  # 7d

    # Groq
    groq_api_key: str = ""
    groq_model_primary: str = "llama-3.1-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"

    # WhatsApp
    whatsapp_service_url: str = "http://localhost:8001"
    whatsapp_session_path: str = "./sessions"

    # M-Pesa (mock MVP)
    mpesa_consumer_key: str = "mock"
    mpesa_consumer_secret: str = "mock"
    mpesa_passkey: str = "mock"
    mpesa_shortcode: str = "mock"

    # Encryption
    encryption_key: str = Field(default="dev-only-change-me-in-production!!")

    # Sentry
    sentry_dsn: str | None = None

    # Ollama fallback
    ollama_base_url: str = "http://localhost:11434"

    # Scraping — use mock data when Playwright sources are blocked
    use_mock_scraper: bool = False

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_url_str(self) -> str:
        return str(self.database_url)

    @property
    def redis_url_str(self) -> str:
        return str(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
