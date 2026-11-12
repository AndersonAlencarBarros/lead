from sqlalchemy import select

from dominio.agregados.lead import Lead
from infraestrutura.orm.orm_lead import leads_tabela  # noqa: F401
from repositorio import Repositorio


class LeadDominioRepositorio(Repositorio):
    """Repositório de domínio (escrita e mutação do agregado Lead)."""

    async def salvar(self, lead: Lead) -> Lead:
        """Persiste ou atualiza o agregado Lead."""
        self.session.add(lead)
        await self.session.flush()
        await self.session.refresh(lead)
        return lead


class LeadLeituraRepositorio(Repositorio):
    """Repositório de leitura (consultas de Lead)."""

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

    async def listar_por_empresa(self, empresa_id) -> list[Lead]:
        stmt = select(Lead).where(Lead.empresa_id == empresa_id)
        resultado = await self.session.execute(stmt)
        return list(resultado.scalars().all())
