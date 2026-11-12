from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from infraestrutura.session import Session
from repositorio.agendamento import (
    AgendamentoDominioRepositorio,
    AgendamentoLeituraRepositorio,
)
from repositorio.auditoria import (
    AuditoriaDominioRepositorio,
    AuditoriaLeituraRepositorio,
)
from repositorio.conversa import ConversaDominioRepositorio, ConversaLeituraRepositorio
from repositorio.empresa import EmpresaDominioRepositorio, EmpresaLeituraRepositorio
from repositorio.lead import LeadDominioRepositorio, LeadLeituraRepositorio
from repositorio.turno_ia import TurnoDominioRepositorio, TurnoLeituraRepositorio


class ParRepositorio[TDominio, TLeitura](NamedTuple):
    """Tupla de tipos contendo (repositório_domínio, repositório_leitura)."""

    dominio: type[TDominio]
    leitura: type[TLeitura]


class Dominio:
    """Catálogo de domínios com tuplas (repositório de domínio, repositório de leitura)."""

    AGENDAMENTO = ParRepositorio(
        dominio=AgendamentoDominioRepositorio,
        leitura=AgendamentoLeituraRepositorio,
    )
    CONVERSA = ParRepositorio(
        dominio=ConversaDominioRepositorio,
        leitura=ConversaLeituraRepositorio,
    )
    EMPRESA = ParRepositorio(
        dominio=EmpresaDominioRepositorio,
        leitura=EmpresaLeituraRepositorio,
    )
    LEAD = ParRepositorio(
        dominio=LeadDominioRepositorio,
        leitura=LeadLeituraRepositorio,
    )
    TURNO = ParRepositorio(
        dominio=TurnoDominioRepositorio,
        leitura=TurnoLeituraRepositorio,
    )
    AUDITORIA = ParRepositorio(
        dominio=AuditoriaDominioRepositorio,
        leitura=AuditoriaLeituraRepositorio,
    )


class UnidadeDeTrabalho[TDominio, TLeitura]:
    """Unidade de Trabalho (Unit of Work) para controle transacional e injeção de repositórios.

    Uso:
        async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
            conversa = await uow.leitura.buscar_por_id_e_telefone(
                "empresa_id", "telefone"
            )
            ...
            await uow.dominio.salvar(conversa)
            await uow.commit()
    """

    def __init__(
        self,
        dominio: ParRepositorio[TDominio, TLeitura]
        | tuple[type[TDominio], type[TLeitura]],
    ) -> None:
        self._repo_dominio_cls: type[TDominio] = dominio[0]
        self._repo_leitura_cls: type[TLeitura] = dominio[1]
        self._session_ctx: Session | None = None
        self.session: AsyncSession | None = None
        self.dominio: TDominio | None = None
        self.leitura: TLeitura | None = None

    async def __aenter__(self) -> "UnidadeDeTrabalho[TDominio, TLeitura]":
        self._session_ctx = Session()
        self.session = await self._session_ctx.__aenter__()
        self.dominio = self._repo_dominio_cls(self.session)
        self.leitura = self._repo_leitura_cls(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session_ctx is not None:
            await self._session_ctx.__aexit__(exc_type, exc_val, exc_tb)

    async def commit(self) -> None:
        """Efetiva a transação atual na sessão."""
        if self.session is not None:
            await self.session.commit()

    async def rollback(self) -> None:
        """Reverte a transação atual na sessão."""
        if self.session is not None:
            await self.session.rollback()
