"""
Octs AI - Application Configuration & Settings
Uses Pydantic Settings for strictly-typed, environment-driven configuration.
"""

from functools import lru_cache
from typing import List, Optional, Set
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration management for Octs AI.
    Loads from .env and environment variables with defensive defaults.
    """

    # Model Provider Settings
    gemini_api_key: Optional[str] = None
    model_name: str = "gemini-3.5-flash-lite"
    model_provider: str = "google_genai"
    model_temperature: float = 0.0

    # LangSmith Observability Settings
    langsmith_tracing: bool = False
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "octs-ai"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Security & CORS Settings
    cors_origins: List[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Valid Creative Disciplines (as identified from the codebase)
    allowed_disciplines: Set[str] = {
        "writers",
        "musicians",
        "creators",
        "designers",
    }

    # Bounded execution limits
    max_recursion_limit: int = 15
    max_recovery_attempts: int = 2
    max_prompt_length: int = 50000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            # Split comma-separated string if provided in env
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def is_langsmith_active(self) -> bool:
        """Determines if LangSmith tracing is explicitly enabled and properly configured."""
        return bool(self.langsmith_tracing and self.langsmith_api_key and self.langsmith_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
