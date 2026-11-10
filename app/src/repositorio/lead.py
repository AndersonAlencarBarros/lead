from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dominio.agregados.lead import Lead
from infraestrutura.orm.orm_lead import leads_tabela  # noqa: F401


class LeadDominioRepositorio:
    """Repositório de domínio (escrita e mutação do agregado Lead)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def salvar(self, lead: Lead) -> Lead:
        """Persiste ou atualiza o agregado Lead."""
        self.session.add(lead)
        await self.session.flush()
        await self.session.refresh(lead)
        return lead


class LeadLeituraRepositorio:
    """Repositório de leitura (consultas de Lead)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def buscar_por_id(self, lead_id) -> Lead | None:
        stmt = select(Lead).where(Lead.id == lead_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()

    async def buscar_por_empresa_e_telefone(
        self, empresa_id, telefone: str
    ) -> Lead | None:
        stmt = select(Lead).where(
            (Lead.empresa_id == empresa_id) & (Lead.telefone == telefone)
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
