from datetime import datetime

import httpx

import main
from dominio.agregados.conversa import Conversa
from dominio.agregados.turno_ia import StatusTurno, TurnoIA
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
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
        cidades_atendidas=["Recife"],
        estagios=["Novo", "Qualificado", "Humano"],
        playbook=EXEMPLO_PLAYBOOK_SOL_NASCENTE,
    )


async def test_metricas_do_tenant(db_session):
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa = await criar_empresa(_empresa_payload(), uow)
        await uow.commit()

    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        lead = await criar_lead(
            empresa.id,
            uow,
            telefone="11988887777",
            tags=["qualificado"],
        )
        await uow.commit()

    conversa = Conversa(
        tenant_id=empresa.tenant_id,
        telefone="11988887777",
        lead_id=lead.id,
    )
    conversa.ativar_intervencao_humana()
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa = await uow.dominio.salvar(conversa)
        await uow.commit()

    async with UnidadeDeTrabalho(Dominio.TURNO) as uow:
        await uow.dominio.salvar(
            TurnoIA(
                conversa_id=conversa.id,
                tenant_id=empresa.tenant_id,
                mensagem_origem_id="msg-1",
                status=StatusTurno.CONCLUIDO,
                modelo="fake",
                tokens_entrada=10,
                tokens_saida=5,
                custo_estimado=0.5,
                latencia_ms=100,
                criado_em=datetime.now(),
            )
        )
        await uow.commit()

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resposta = await client.get("/metricas/empresa-1")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "tenant_id": "empresa-1",
        "total_conversas": 1,
        "custo_medio_por_conversa": 0.5,
        "percentual_qualificados": 100.0,
        "percentual_transferidos": 100.0,
    }
