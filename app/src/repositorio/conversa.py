
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dominio.agregados.conversa import Conversa
from infraestrutura.orm.orm_conversa import conversas_tabela  # noqa: F401


class ConversaDominioRepositorio:
    """Repositório de domínio (escrita e mutação do agregado Conversa)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def salvar(self, conversa: Conversa) -> Conversa:
        """Persiste ou atualiza o agregado Conversa."""
        self.session.add(conversa)
        await self.session.flush()
        await self.session.refresh(conversa)
        return conversa


class ConversaLeituraRepositorio:
    """Repositório de leitura (consultas e projeções de Conversa)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def buscar_por_empresa_e_telefone(
        self, empresa_id: str, telefone: str
    ) -> Conversa | None:
        """Busca conversa por empresa e telefone, carregando as mensagens associadas."""
        stmt = (
            select(Conversa)
            .where(
                (Conversa.empresa_id == empresa_id)
                & (Conversa.telefone == telefone)
            )
            .options(selectinload(Conversa.mensagens))
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
