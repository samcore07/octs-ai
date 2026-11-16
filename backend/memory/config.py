"""
OCTS AI - Memory Subsystem Configuration
Pydantic Settings managing persistence, retrieval thresholds, and token budgets.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MemorySettings(BaseSettings):
    """
    Configuration parameters governing persistent intelligence and memory lifecycle.
    """
    memory_enabled: bool = Field(default=True, description="Master toggle for memory subsystem.")
    memory_auto_extraction: bool = Field(default=True, description="Whether to automatically extract memories from completed interactions.")
    memory_retrieval_enabled: bool = Field(default=True, description="Whether to retrieve and inject relevant memories into specialist prompts.")
    memory_max_retrieved: int = Field(default=10, ge=1, le=50, description="Maximum count of memory records to inject per query.")
    memory_max_context_tokens: int = Field(default=2000, ge=100, le=10000, description="Approximate token budget ceiling for injected memory context.")
    memory_relevance_threshold: float = Field(default=0.60, ge=0.0, le=1.0, description="Minimum relevance score for memory inclusion.")
    memory_database_url: str = Field(
        default_factory=lambda: (
            os.getenv("SUPABASE_DB_URL")
            or os.getenv("DATABASE_URL")
            or ("sqlite:////tmp/octs_memory.db" if os.getenv("VERCEL") else "sqlite:///./octs_memory.db")
        ),
        description="SQLAlchemy database connection URI (supports SQLite and Supabase PostgreSQL).",
    )
    memory_extraction_timeout: float = Field(default=10.0, ge=1.0, le=60.0, description="Timeout for memory extraction in seconds.")
    memory_default_owner_id: str = Field(default="default_user", description="Fallback identity identifier.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("memory_database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Database URL cannot be empty.")
        return s
