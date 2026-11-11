from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: float = 30.0
    db_pool_recycle: int = 1800
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    llm_model: str = Field(
        default="ollama/qwen2.5:7b",
        validation_alias="LLM_MODEL",
    )
    llm_api_base: str | None = Field(
        default="http://localhost:11434",
        validation_alias="LLM_API_BASE",
    )
    llm_api_key: str | None = Field(
        default=None,
        validation_alias="LLM_API_KEY",
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        validation_alias="LLM_TEMPERATURE",
    )
    llm_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        validation_alias="LLM_TIMEOUT_SECONDS",
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="CELERY_BROKER_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("database_url")
    @classmethod
    def _use_async_postgres_dialect(cls, value: str) -> str:
        if value.startswith("postgres://"):
            value = "postgresql://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value.removeprefix("postgresql://")
        if value.startswith("sqlite://"):
            value = "sqlite+aiosqlite://" + value.removeprefix("sqlite://")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
