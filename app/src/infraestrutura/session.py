from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_settings


class Session:
    """Gerenciador central de engine, pools de conexão e ciclo de vida de sessões SQLAlchemy."""

    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """Inicializa ou retorna o engine singleton com pool assíncrono."""
        if cls._engine is None:
            settings = get_settings()
            cls._engine = create_async_engine(
                settings.database_url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=settings.db_pool_pre_ping,
                echo=settings.db_echo,
            )
            cls._session_factory = async_sessionmaker(
                cls._engine, expire_on_commit=False
            )
        return cls._engine

    @classmethod
    async def dispose(cls) -> None:
        """Encerra e limpa o pool de conexões do engine."""
        if cls._engine is not None:
            await cls._engine.dispose()
        cls._engine = None
        cls._session_factory = None

    async def __aenter__(self) -> AsyncSession:
        if self._session_factory is None:
            self.get_engine()
        assert self._session_factory is not None
        self._session = self._session_factory()
        return await self._session.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is not None:
            try:
                if exc_type is not None:
                    await self._session.rollback()
                else:
                    await self._session.commit()
            finally:
                await self._session.__aexit__(exc_type, exc_val, exc_tb)
