from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dominio.agregados.agendamento import Agendamento
from infraestrutura.orm.orm_agendamento import agendamentos_tabela  # noqa: F401


class AgendamentoDominioRepositorio:
    """Repositório de domínio (escrita e mutação do agregado Agendamento)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def salvar(self, agendamento: Agendamento) -> Agendamento:
        """Persiste ou atualiza o agregado Agendamento."""
        self.session.add(agendamento)
        await self.session.flush()
        await self.session.refresh(agendamento)
        return agendamento


class AgendamentoLeituraRepositorio:
    """Repositório de leitura (consultas de Agendamento)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def buscar_por_id(self, agendamento_id) -> Agendamento | None:
        stmt = select(Agendamento).where(Agendamento.id == agendamento_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
