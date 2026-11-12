from sqlalchemy import select

from dominio.agregados.auditoria import Auditoria
from infraestrutura.orm.orm_auditoria import (  # noqa: F401
    auditorias_tabela,
)
from repositorio import Repositorio


class AuditoriaDominioRepositorio(Repositorio):
    """Repositório de escrita das auditorias."""

    async def salvar(self, auditoria: Auditoria) -> Auditoria:
        self.session.add(auditoria)
        await self.session.flush()
        await self.session.refresh(auditoria)
        return auditoria


class AuditoriaLeituraRepositorio(Repositorio):
    """Consultas das auditorias."""

    async def listar_por_turno(self, turno_id) -> list[Auditoria]:
        stmt = (
            select(Auditoria)
            .where(Auditoria.turno_id == turno_id)
            .order_by(Auditoria.criado_em)
        )
        resultado = await self.session.execute(stmt)
        return list(resultado.scalars().all())

    async def buscar_por_turno_ferramenta_hash(
        self,
        turno_id,
        ferramenta: str,
        hash_argumentos: str,
    ) -> Auditoria | None:
        stmt = select(Auditoria).where(
            (Auditoria.turno_id == turno_id)
            & (Auditoria.ferramenta == ferramenta)
            & (Auditoria.hash_argumentos == hash_argumentos)
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
