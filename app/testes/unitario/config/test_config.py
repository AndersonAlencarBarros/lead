import pytest

from config import ProvedorLLM, Settings


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
    monkeypatch.setenv("LLM_MODEL", "openrouter/liquid/lfm-3-1.7b:free")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert settings.llm_api_key == "chave-openrouter"
    assert settings.llm_model == "openrouter/liquid/lfm-3-1.7b:free"


def test_settings_resolvem_preset_openrouter():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./db.sqlite3",
        LLM_PROVIDER="openrouter",
    )

    assert settings.llm_provider is ProvedorLLM.OPENROUTER
    assert settings.llm_model == "openrouter/liquid/lfm-3-1.7b:free"
    assert settings.llm_api_base is None


def test_settings_resolvem_preset_deepseek_com_chave():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./db.sqlite3",
        LLM_PROVIDER="deepseek",
        DEEPSEEK_API_KEY="chave-deepseek",
    )

    assert settings.llm_provider is ProvedorLLM.DEEPSEEK
    assert settings.llm_model == "deepseek/deepseek-chat"
    assert settings.llm_api_key == "chave-deepseek"


def test_settings_resolvem_preset_ollama_sem_chave():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./db.sqlite3",
        LLM_PROVIDER="ollama",
    )

    assert settings.llm_provider is ProvedorLLM.OLLAMA
    assert settings.llm_model == "ollama/qwen2.5"
    assert settings.llm_api_base == "http://localhost:11434"
    assert settings.llm_api_key is None


def test_settings_override_de_modelo_e_base_tem_prioridade():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./db.sqlite3",
        LLM_PROVIDER="ollama",
        LLM_MODEL="ollama/llama3.2",
        LLM_API_BASE="http://host.docker.internal:11434",
    )

    assert settings.llm_model == "ollama/llama3.2"
    assert settings.llm_api_base == "http://host.docker.internal:11434"


def test_settings_llm_api_key_generica_tem_prioridade():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./db.sqlite3",
        LLM_PROVIDER="deepseek",
        DEEPSEEK_API_KEY="chave-deepseek",
        LLM_API_KEY="chave-generica",
    )

    assert settings.llm_api_key == "chave-generica"
