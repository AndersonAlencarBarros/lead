from datetime import datetime
from uuid import uuid4

import pytest

from exceptions import AgendamentoNaoEncontrado
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.agendamento import (
    buscar_agendamento,
    cancelar_agendamento,
    confirmar_agendamento,
    criar_agendamento,
)
from servicos.executores.empresa import criar_empresa
from servicos.executores.lead import criar_lead
from servicos.serializadores.empresa import (
    EXEMPLO_PLAYBOOK_SOL_NASCENTE,
    EmpresaCriacaoSerializador,
)


def _empresa_payload() -> EmpresaCriacaoSerializador:
    return EmpresaCriacaoSerializador(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status="ativa",
        telefone_notificacao="11999999999",
        configuracao_ia={
            "tom": "informal",
            "pode_dizer_que_e_ia": True,
            "nome_assistente": "Ana",
            "horario_atendimento_ia": {
                "horario_inicio": "2026-01-01T08:00:00",
                "horario_fim": "2026-01-01T18:00:00",
            },
        },
        regras_gerais=[],
        cidades_atendidas=[],
        estagios=[],
        playbook=EXEMPLO_PLAYBOOK_SOL_NASCENTE,
    )


async def _criar_empresa_e_lead():
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa = await criar_empresa(_empresa_payload(), uow)
        await uow.commit()

    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        lead = await criar_lead(
            empresa.id,
            uow,
            nome="Maria",
            telefone="11988887777",
        )
        await uow.commit()

    return empresa, lead


async def test_cria_busca_confirma_e_cancela_agendamento():
    empresa, lead = await _criar_empresa_e_lead()
    horario = datetime(2026, 1, 2, 10, 0)

    async with UnidadeDeTrabalho(Dominio.AGENDAMENTO) as uow:
        agendamento = await criar_agendamento(
            empresa.id,
            lead.id,
            "11988887777",
            horario,
            uow,
        )
        await uow.commit()

    assert agendamento.id is not None
    assert agendamento.status.value == "confirmado"

    async with UnidadeDeTrabalho(Dominio.AGENDAMENTO) as uow:
        encontrado = await buscar_agendamento(agendamento.id, uow)
    assert encontrado.id == agendamento.id

    async with UnidadeDeTrabalho(Dominio.AGENDAMENTO) as uow:
        cancelado = await cancelar_agendamento(agendamento.id, uow)
        await uow.commit()
    assert cancelado.status.value == "cancelado"

    async with UnidadeDeTrabalho(Dominio.AGENDAMENTO) as uow:
        confirmado = await confirmar_agendamento(agendamento.id, uow)
        await uow.commit()
    assert confirmado.status.value == "confirmado"

    assert encontrado.horario_agendado == horario


async def test_agendamento_inexistente_retorna_erro():
    with pytest.raises(AgendamentoNaoEncontrado):
        async with UnidadeDeTrabalho(Dominio.AGENDAMENTO) as uow:
            await buscar_agendamento(uuid4(), uow)
