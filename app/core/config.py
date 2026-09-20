"""
Application Configuration
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "CancerInfo API"
    APP_DESCRIPTION: str = (
        "A free, structured, global, source-transparent public REST API aggregating "
        "normalized cancer knowledge with fact-level provenance from authoritative health organizations."
    )
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = "development"

    # Database configuration (PostgreSQL / Neon / SQLite)
    DATABASE_URL: str = "sqlite:///./cancerinfo.db"

    # Security & Admin
    ADMIN_API_KEY: str = "dev-admin-secret-key"
    RATE_LIMIT_PER_MINUTE: int = 120

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # type: ignore
        return ["*"]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
