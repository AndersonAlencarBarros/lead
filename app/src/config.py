from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProvedorLLM(StrEnum):
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


@dataclass(frozen=True)
class PerfilLLM:
    modelo: str
    api_base: str | None = None


PERFIS_LLM = {
    ProvedorLLM.OPENROUTER: PerfilLLM(
        modelo="openrouter/liquid/lfm-3-1.7b:free",
    ),
    ProvedorLLM.DEEPSEEK: PerfilLLM(
        modelo="deepseek/deepseek-chat",
    ),
    ProvedorLLM.OLLAMA: PerfilLLM(
        modelo="ollama/qwen2.5",
        api_base="http://localhost:11434",
    ),
}


class Settings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: float = 30.0
    db_pool_recycle: int = 1800
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    llm_provider: ProvedorLLM = Field(
        default=ProvedorLLM.OPENROUTER,
        validation_alias="LLM_PROVIDER",
    )
    llm_model: str | None = Field(
        default=None,
        validation_alias="LLM_MODEL",
    )
    llm_api_base: str | None = Field(
        default=None,
        validation_alias="LLM_API_BASE",
    )
    llm_api_key: str | None = Field(
        default=None,
        validation_alias="LLM_API_KEY",
    )
    open_router_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPEN_ROUTER_KEY", "OPENROUTER_API_KEY"),
    )
    deepseek_api_key: str | None = Field(
        default=None,
        validation_alias="DEEPSEEK_API_KEY",
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
    llm_preco_entrada_por_milhao: float = Field(
        default=0.2,
        ge=0,
        validation_alias="LLM_PRECO_ENTRADA_POR_MILHAO",
    )
    llm_preco_saida_por_milhao: float = Field(
        default=0.1,
        ge=0,
        validation_alias="LLM_PRECO_SAIDA_POR_MILHAO",
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

    @model_validator(mode="after")
    def _resolver_perfil_llm(self):
        perfil = PERFIS_LLM[self.llm_provider]

        if not self.llm_model:
            self.llm_model = perfil.modelo
        if not self.llm_api_base:
            self.llm_api_base = perfil.api_base
        if not self.llm_api_key:
            if self.llm_provider is ProvedorLLM.OPENROUTER:
                self.llm_api_key = self.open_router_key
            elif self.llm_provider is ProvedorLLM.DEEPSEEK:
                self.llm_api_key = self.deepseek_api_key

        return self

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
