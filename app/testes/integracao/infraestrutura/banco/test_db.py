from sqlalchemy import text
from sqlalchemy.engine import make_url


async def test_select_1(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1


async def test_connects_to_the_container_database(db_session, database_url):
    expected = make_url(database_url).database
    result = await db_session.execute(text("SELECT current_database()"))
    assert result.scalar_one() == expected


async def test_engine_uses_the_async_psycopg_driver(db_session):
    assert db_session.get_bind().dialect.name == "postgresql"
    assert db_session.get_bind().driver == "psycopg"
