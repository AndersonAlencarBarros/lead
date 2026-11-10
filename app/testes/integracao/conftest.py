import os

import pytest
from sqlalchemy import text
from testcontainers.community.postgres import PostgresContainer

import infraestrutura.orm  # noqa: F401
from config import get_settings
from infraestrutura.base import Base
from infraestrutura.session import Session


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def database_url(postgres_container):
    url = postgres_container.get_connection_url()
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    return url


@pytest.fixture
async def db_session(database_url):
    # O engine é descartado a cada teste: o pool fica preso ao event loop
    # em que foi criado, e o pytest-asyncio usa um loop novo por teste.
    await Session.dispose()
    async with Session() as session:
        yield session
    await Session.dispose()


@pytest.fixture(autouse=True)
async def reset_banco(database_url):
    await Session.dispose()
    engine = Session.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "sqlite":
            await conn.execute(text("DELETE FROM agendamentos"))
            await conn.execute(text("DELETE FROM leads"))
            await conn.execute(text("DELETE FROM mensagens"))
            await conn.execute(text("DELETE FROM conversas"))
            await conn.execute(text("DELETE FROM empresas"))
        else:
            await conn.execute(
                text(
                    "TRUNCATE TABLE agendamentos, leads, mensagens, "
                    "conversas, empresas CASCADE"
                )
            )
    await Session.dispose()
    yield
    await Session.dispose()
