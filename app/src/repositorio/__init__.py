from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession


class Repositorio(ABC):
    """Base abstrata para repositórios com sessão SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
