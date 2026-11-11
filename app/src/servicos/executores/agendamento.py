from datetime import datetime
from uuid import UUID

from dominio.agregados.agendamento import Agendamento
from dominio.objetos_de_valor.agendamento import StatusDoAgendamento
from exceptions import AgendamentoNaoEncontrado
from infraestrutura import UnidadeDeTrabalho
from repositorio.agendamento import (
    AgendamentoDominioRepositorio,
    AgendamentoLeituraRepositorio,
)


async def criar_agendamento(
    empresa_id: UUID,
    lead_id: UUID,
    telefone: str,
    horario_agendado: datetime,
    uow: UnidadeDeTrabalho,
    status: StatusDoAgendamento = StatusDoAgendamento.CONFIRMADO,
) -> Agendamento:
    repo_dominio: AgendamentoDominioRepositorio = uow.dominio

    agendamento = Agendamento(
        empresa_id=empresa_id,
        lead_id=lead_id,
        telefone=telefone,
        horario_agendado=horario_agendado,
        status=status,
    )
    return await repo_dominio.salvar(agendamento)


async def buscar_agendamento(
    agendamento_id: UUID,
    uow: UnidadeDeTrabalho,
) -> Agendamento:
    repo_leitura: AgendamentoLeituraRepositorio = uow.leitura
    agendamento = await repo_leitura.buscar_por_id(agendamento_id)
    if agendamento is None:
        raise AgendamentoNaoEncontrado()
    return agendamento


async def confirmar_agendamento(
    agendamento_id: UUID,
    uow: UnidadeDeTrabalho,
) -> Agendamento:
    repo_dominio: AgendamentoDominioRepositorio = uow.dominio
    agendamento = await buscar_agendamento(agendamento_id, uow)
    agendamento.confirmar_agendamento()
    return await repo_dominio.salvar(agendamento)


async def cancelar_agendamento(
    agendamento_id: UUID,
    uow: UnidadeDeTrabalho,
) -> Agendamento:
    repo_dominio: AgendamentoDominioRepositorio = uow.dominio
    agendamento = await buscar_agendamento(agendamento_id, uow)
    agendamento.cancelar_agendamento()
    return await repo_dominio.salvar(agendamento)
