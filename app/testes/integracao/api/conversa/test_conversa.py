import asyncio
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy import select

import main
from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem, Telefone
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho

LEAD_ID = UUID("11111111-1111-1111-1111-111111111111")


def _payload(
    message_id: str,
    texto: str = "oi",
    timestamp: str = "2026-01-01T10:00:00",
) -> dict[str, str]:
    return {
        "message_id": message_id,
        "tenant_id": "empresa-1",
        "telefone": "11988887777",
        "texto": texto,
        "timestamp": timestamp,
    }


async def _criar_conversa() -> Conversa:
    conversa = Conversa(
        tenant_id="empresa-1",
        lead_id=LEAD_ID,
        telefone=Telefone("11999999999"),
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-2",
                conversa_id=None,
                texto="segunda",
                foi_enviada_pela_ia=True,
                foi_enviada_pelo_humano=False,
                criado_em=datetime(2026, 1, 1, 10, 5),
            ),
            Mensagem(
                identificador_da_mensagem="msg-1",
                conversa_id=None,
                texto="primeira",
                foi_enviada_pela_ia=False,
                foi_enviada_pelo_humano=False,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
        ],
        criado_em=datetime(2026, 1, 1, 9, 0),
    )
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        salva = await uow.dominio.salvar(conversa)
        await uow.commit()
    return salva


async def _get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


async def _post_mensagem(payload: dict[str, str]) -> httpx.Response:
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/webhook/mensagem", json=payload)


async def test_webhook_cria_conversa_e_mensagem(db_session):
    resposta = await _post_mensagem(_payload("msg-webhook-1"))

    assert resposta.status_code == 201

    conversa = (await db_session.execute(select(Conversa))).scalar_one()
    mensagem = (await db_session.execute(select(Mensagem))).scalar_one()
    assert mensagem.conversa_id == conversa.id


async def test_webhook_duplicado_e_idempotente():
    payload = _payload("msg-duplicada")

    primeira = await _post_mensagem(payload)
    segunda = await _post_mensagem(payload)

    assert primeira.status_code == 201
    assert segunda.status_code == 204

    dados = (await _get("/conversas/empresa-1/11988887777")).json()
    assert len(dados["mensagens"]) == 1


async def test_webhook_mesmo_telefone_mensagens_diferentes():
    primeira = await _post_mensagem(_payload("msg-a", timestamp="2026-01-01T10:00:00"))
    segunda = await _post_mensagem(_payload("msg-b", timestamp="2026-01-01T10:01:00"))

    assert primeira.status_code == 201
    assert segunda.status_code == 201

    dados = (await _get("/conversas/empresa-1/11988887777")).json()
    assert len(dados["mensagens"]) == 2
    assert [
        mensagem["identificador_da_mensagem"] for mensagem in dados["mensagens"]
    ] == ["msg-a", "msg-b"]


async def test_webhook_concorrente_cria_uma_conversa():
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        respostas = await asyncio.gather(
            client.post("/webhook/mensagem", json=_payload("msg-concorrente")),
            client.post("/webhook/mensagem", json=_payload("msg-concorrente")),
        )

    assert sorted(resposta.status_code for resposta in respostas) == [201, 204]

    dados = (await _get("/conversas/empresa-1/11988887777")).json()
    assert len(dados["mensagens"]) == 1


async def test_get_conversa_retorna_mensagens_associadas():
    conversa = await _criar_conversa()

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["id"] == str(conversa.id)
    assert dados["lead_id"] == str(LEAD_ID)
    assert [
        mensagem["identificador_da_mensagem"] for mensagem in dados["mensagens"]
    ] == ["msg-1", "msg-2"]


async def test_get_conversa_inexistente_retorna_404():
    resposta = await _get("/conversas/empresa-inexistente/11999999999")

    assert resposta.status_code == 404
