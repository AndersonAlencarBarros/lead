import httpx
from sqlalchemy import select

import main
from dominio.agregados.empresa import Empresa
from servicos.serializadores.empresa import (
    EXEMPLO_EMPRESA_CONFEITARIA,
    EXEMPLO_PLAYBOOK_SOL_NASCENTE,
)


def _payload() -> dict:
    return {
        "tenant_id": "empresa-1",
        "nome": "Empresa 1",
        "status": "ativa",
        "telefone_notificacao": "11999999999",
        "janela_de_resposta": 10,
        "configuracao_ia": {
            "tom": "informal",
            "pode_dizer_que_e_ia": True,
            "nome_assistente": "Ana",
            "horario_atendimento_ia": {
                "horario_inicio": "2026-01-01T08:00:00",
                "horario_fim": "2026-01-01T18:00:00",
            },
        },
        "regras_gerais": ["responder em português"],
        "cidades_atendidas": ["São Paulo"],
        "estagios": ["qualificado", "agendado"],
        "playbook": EXEMPLO_PLAYBOOK_SOL_NASCENTE,
    }


async def _post_empresa(payload: dict) -> httpx.Response:
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/empresas", json=payload)


async def test_cria_empresa(db_session):
    resposta = await _post_empresa(_payload())

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["tenant_id"] == "empresa-1"
    assert dados["nome"] == "Empresa 1"
    assert dados["status"] == "ativa"
    assert dados["configuracao_ia"]["tom"] == "informal"
    assert dados["configuracao_ia"]["horario_atendimento_ia"] == {
        "horario_inicio": "2026-01-01T08:00:00",
        "horario_fim": "2026-01-01T18:00:00",
    }
    assert dados["cidades_atendidas"] == ["São Paulo"]

    empresa = (await db_session.execute(select(Empresa))).scalar_one()
    assert empresa.configuracoes.configuracao_ia.nome_assistente == "Ana"


async def test_cria_empresa_confeitaria(db_session):
    resposta = await _post_empresa(EXEMPLO_EMPRESA_CONFEITARIA)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["tenant_id"] == "confeitaria-encanto"
    assert dados["nome"] == "Confeitaria Encanto"
    assert dados["janela_de_resposta"] == 5
    assert dados["configuracao_ia"]["tom"] == "formal"
    assert dados["configuracao_ia"]["pode_dizer_que_e_ia"] is False
    assert dados["playbook"]["nome"] == "confeitaria-sob-encomenda"
    assert "mover_estagio" in dados["playbook"]["ferramentas"]
    assert "atualizar_lead" in dados["playbook"]["ferramentas"]
    assert "adicionar_tag" not in dados["playbook"]["ferramentas"]
    assert "atualizar_ficha" not in dados["playbook"]["ferramentas"]


async def test_empresa_duplicada_retorna_409():
    assert (await _post_empresa(_payload())).status_code == 201

    resposta = await _post_empresa(_payload())

    assert resposta.status_code == 409


async def test_intervalo_invalido_retorna_422():
    payload = _payload()
    payload["configuracao_ia"]["horario_atendimento_ia"] = {
        "horario_inicio": "2026-01-01T18:00:00",
        "horario_fim": "2026-01-01T08:00:00",
    }

    resposta = await _post_empresa(payload)

    assert resposta.status_code == 422
