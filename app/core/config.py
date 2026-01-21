"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    api_prefix: str = "/api"
    debug: bool = False
    app_name: str = "Contractify API"
    app_version: str = "1.0.0"

    # Database
    database_url: str

    @property
    def database_url_sync(self) -> str:
        """Convert async database URL to sync for Alembic migrations."""
        # Replace postgresql+asyncpg:// with postgresql:// for psycopg2
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

    # CORS
    cors_origins: str

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Firebase
    firebase_project_id: str
    firebase_private_key_id: str
    firebase_private_key: str
    firebase_client_email: str
    firebase_client_id: str
    firebase_auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    firebase_token_uri: str = "https://oauth2.googleapis.com/token"

    # External Services
    openai_api_key: str
    sendgrid_api_key: str

    @property
    def firebase_credentials(self) -> dict:
        """Build Firebase credentials dict from env vars."""
        if not self.firebase_project_id:
            return {}
        return {
            "type": "service_account",
            "project_id": self.firebase_project_id,
            "private_key_id": self.firebase_private_key_id,
            "private_key": self.firebase_private_key.replace("\\n", "\n"),
            "client_email": self.firebase_client_email,
            "client_id": self.firebase_client_id,
            "auth_uri": self.firebase_auth_uri,
            "token_uri": self.firebase_token_uri,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
