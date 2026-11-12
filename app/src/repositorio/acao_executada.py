from sqlalchemy import select

from dominio.agregados.acao_executada import AcaoExecutada
from infraestrutura.orm.orm_acao_executada import (  # noqa: F401
    acoes_executadas_tabela,
)
from repositorio import Repositorio


class AcaoDominioRepositorio(Repositorio):
    """Repositório de escrita das ações executadas."""

    async def salvar(self, acao: AcaoExecutada) -> AcaoExecutada:
        self.session.add(acao)
        await self.session.flush()
        await self.session.refresh(acao)
        return acao


class AcaoLeituraRepositorio(Repositorio):
    """Consultas das ações executadas."""

    async def listar_por_turno(self, turno_id) -> list[AcaoExecutada]:
        stmt = (
            select(AcaoExecutada)
            .where(AcaoExecutada.turno_id == turno_id)
            .order_by(AcaoExecutada.criado_em)
        )
        resultado = await self.session.execute(stmt)
        return list(resultado.scalars().all())

    async def buscar_por_turno_ferramenta_hash(
        self,
        turno_id,
        ferramenta: str,
        hash_argumentos: str,
    ) -> AcaoExecutada | None:
        stmt = select(AcaoExecutada).where(
            (AcaoExecutada.turno_id == turno_id)
            & (AcaoExecutada.ferramenta == ferramenta)
            & (AcaoExecutada.hash_argumentos == hash_argumentos)
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
