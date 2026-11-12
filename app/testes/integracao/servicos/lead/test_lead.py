import pytest

from exceptions import LeadJaCadastrado
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.empresa import criar_empresa
from servicos.executores.lead import buscar_lead, criar_lead
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


async def _criar_empresa():
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa = await criar_empresa(_empresa_payload(), uow)
        await uow.commit()
    return empresa


async def test_cria_e_busca_lead():
    empresa = await _criar_empresa()

    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        lead = await criar_lead(
            empresa.id,
            uow,
            nome="Maria",
            telefone="11988887777",
            cidade="São Paulo",
            estagio="qualificado",
        )
        await uow.commit()

    assert lead.id is not None
    assert lead.empresa_id == empresa.id
    assert lead.nome == "Maria"

    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        encontrado = await buscar_lead(lead.id, uow)

    assert encontrado.id == lead.id
    assert encontrado.telefone == "11988887777"
    assert str(encontrado.estagio) == "qualificado"


async def test_lead_duplicado_retorna_erro():
    empresa = await _criar_empresa()

    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        await criar_lead(empresa.id, uow, telefone="11988887777")
        await uow.commit()

    with pytest.raises(LeadJaCadastrado):
        async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
            await criar_lead(empresa.id, uow, telefone="11988887777")
