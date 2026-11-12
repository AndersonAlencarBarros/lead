import pytest

from config import Settings


@pytest.mark.parametrize(
    "database_url",
    [
        "postgres://user:pass@host:5432/infraestrutura",
        "postgresql://user:pass@host:5432/infraestrutura",
        "postgresql+psycopg://user:pass@host:5432/infraestrutura",
        "postgresql://user:pass@host/infraestrutura?sslmode=require",
    ],
)
def test_settings_use_the_async_postgres_dialect(database_url):
    settings = Settings(DATABASE_URL=database_url)
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_settings_keep_the_query_string():
    settings = Settings(
        DATABASE_URL="postgres://user:pass@host/infraestrutura?sslmode=require"
    )
    assert settings.database_url.endswith("?sslmode=require")


def test_pool_settings_are_overridable_by_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host/infraestrutura")
    monkeypatch.setenv("DB_POOL_SIZE", "2")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "0")
    settings = Settings()
    assert settings.db_pool_size == 2
    assert settings.db_max_overflow == 0


def test_settings_read_open_router_key(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./db.sqlite3")
    monkeypatch.setenv("OPEN_ROUTER_KEY", "chave-openrouter")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    settings = Settings()
    assert settings.llm_api_key == "chave-openrouter"
    assert settings.llm_model == "openrouter/liquid/lfm-3-1.7b:free"
