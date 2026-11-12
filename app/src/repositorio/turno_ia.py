from sqlalchemy import select

from dominio.agregados.turno_ia import TurnoIA
from infraestrutura.orm.orm_turno_ia import turnos_ia_tabela  # noqa: F401
from repositorio import Repositorio


class TurnoDominioRepositorio(Repositorio):
    """Repositório de domínio para turnos de IA."""

    async def salvar(self, turno: TurnoIA) -> TurnoIA:
        self.session.add(turno)
        await self.session.flush()
        await self.session.refresh(turno)
        return turno


class TurnoLeituraRepositorio(Repositorio):
    """Consultas de turnos de IA."""

    async def buscar_por_id(self, turno_id) -> TurnoIA | None:
        stmt = select(TurnoIA).where(TurnoIA.id == turno_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()

    async def buscar_por_conversa_e_mensagem(
        self,
        conversa_id,
        mensagem_origem_id: str,
    ) -> TurnoIA | None:
        stmt = select(TurnoIA).where(
            (TurnoIA.conversa_id == conversa_id)
            & (TurnoIA.mensagem_origem_id == mensagem_origem_id)
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
