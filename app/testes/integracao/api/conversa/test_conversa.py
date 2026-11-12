import asyncio
from datetime import datetime

import httpx
from sqlalchemy import select

import main
from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.agregados.lead import Lead
from dominio.objetos_de_valor.conversa import Mensagem, Telefone
from dominio.objetos_de_valor.empresa import (
    ConfiguracaoIA,
    Intervalo,
    StatusEmpresa,
    TomDaIA,
)
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from testes.apoio import playbook_solar


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


async def _criar_conversa(
    mensagens: list[Mensagem] | None = None,
    teve_intervencao_humana: bool = False,
) -> Conversa:
    empresa = Empresa(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status=StatusEmpresa.ATIVA,
        telefone_notificacao="11999999999",
        configuracao_ia=ConfiguracaoIA(
            tom=TomDaIA.INFORMAL,
            pode_dizer_que_e_ia=True,
            nome_assistente="Ana",
            horario_atendimento_ia=Intervalo(
                horario_inicio=datetime(2026, 1, 1, 8, 0),
                horario_fim=datetime(2026, 1, 1, 18, 0),
            ),
        ),
        regras_gerais=[],
        cidades_atendidas=[],
        estagios=[],
        playbook=playbook_solar(),
    )
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa_salva = await uow.dominio.salvar(empresa)
        await uow.commit()

    lead = Lead(empresa_id=empresa_salva.id, nome="Lead 1")
    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        lead_salvo = await uow.dominio.salvar(lead)
        await uow.commit()

    conversa = Conversa(
        tenant_id="empresa-1",
        lead_id=lead_salvo.id,
        telefone=Telefone("11999999999"),
        mensagens=mensagens
        if mensagens is not None
        else [
            Mensagem(
                identificador_da_mensagem="msg-2",
                conversa_id=None,
                texto="segunda",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 5),
            ),
            Mensagem(
                identificador_da_mensagem="msg-1",
                conversa_id=None,
                texto="primeira",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
        ],
        criado_em=datetime(2026, 1, 1, 9, 0),
    )
    conversa.teve_intervencao_humana = teve_intervencao_humana
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


async def _post_intervencao(payload: dict[str, str]) -> httpx.Response:
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/intervencao", json=payload)


async def test_webhook_cria_conversa_e_mensagem(db_session, enfileiramentos):
    resposta = await _post_mensagem(_payload("msg-webhook-1"))

    assert resposta.status_code == 201
    assert enfileiramentos == [("empresa-1", "11988887777", "msg-webhook-1")]

    conversa = (await db_session.execute(select(Conversa))).scalar_one()
    mensagem = (await db_session.execute(select(Mensagem))).scalar_one()
    assert mensagem.conversa_id == conversa.id
    assert mensagem.foi_respondida_pelo_usuario is True
    assert mensagem.foi_intervencao_humana is False


async def test_webhook_duplicado_e_idempotente(db_session, enfileiramentos):
    payload = _payload("msg-duplicada")

    primeira = await _post_mensagem(payload)
    segunda = await _post_mensagem(payload)

    assert primeira.status_code == 201
    assert segunda.status_code == 204
    assert enfileiramentos == [("empresa-1", "11988887777", "msg-duplicada")]

    mensagens = (await db_session.execute(select(Mensagem))).scalars().all()
    assert len(mensagens) == 1


async def test_webhook_com_fila_indisponivel_retorna_503(db_session, monkeypatch):
    from dominio.regras_de_negocio.servico_ia import responder_conversa

    def _falhar(*_args):
        raise RuntimeError("redis fora do ar")

    monkeypatch.setattr(responder_conversa, "criar_resposta_da_ia", _falhar)

    resposta = await _post_mensagem(_payload("msg-sem-fila"))

    assert resposta.status_code == 503
    conversa = (await db_session.execute(select(Conversa))).scalar_one()
    assert conversa.tenant_id == "empresa-1"


async def test_webhook_mesmo_telefone_mensagens_diferentes(db_session):
    primeira = await _post_mensagem(_payload("msg-a", timestamp="2026-01-01T10:00:00"))
    segunda = await _post_mensagem(_payload("msg-b", timestamp="2026-01-01T10:01:00"))

    assert primeira.status_code == 201
    assert segunda.status_code == 201

    mensagens = (
        (await db_session.execute(select(Mensagem).order_by(Mensagem.criado_em)))
        .scalars()
        .all()
    )
    assert [mensagem.identificador_da_mensagem for mensagem in mensagens] == [
        "msg-a",
        "msg-b",
    ]


async def test_webhook_concorrente_cria_uma_conversa(db_session):
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        respostas = await asyncio.gather(
            client.post("/webhook/mensagem", json=_payload("msg-concorrente")),
            client.post("/webhook/mensagem", json=_payload("msg-concorrente")),
        )

    assert sorted(resposta.status_code for resposta in respostas) == [201, 204]

    mensagens = (await db_session.execute(select(Mensagem))).scalars().all()
    assert len(mensagens) == 1


async def test_get_conversa_retorna_ultima_resposta_da_ia():
    conversa = await _criar_conversa()

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["id"] == str(conversa.id)
    assert dados["lead_id"] == str(conversa.lead_id)
    assert [
        mensagem["identificador_da_mensagem"] for mensagem in dados["mensagens"]
    ] == ["msg-2"]
    assert dados["mensagens"][0]["foi_gerada_pela_ia"] is True
    assert dados["mensagens"][0]["foi_respondida_pelo_usuario"] is False
    assert dados["mensagens"][0]["foi_intervencao_humana"] is False


async def test_get_conversa_sem_resposta_da_ia_retorna_404():
    conversa = await _criar_conversa(
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-1",
                texto="primeira",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            )
        ]
    )

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 404


async def test_get_conversa_retorna_resposta_mesmo_com_mensagem_mais_recente_do_lead():
    conversa = await _criar_conversa(
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-1",
                texto="primeira",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
            Mensagem(
                identificador_da_mensagem="msg-2",
                texto="resposta",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 1),
            ),
            Mensagem(
                identificador_da_mensagem="msg-3",
                texto="nova mensagem",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 2),
            ),
        ]
    )

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    assert [
        mensagem["identificador_da_mensagem"]
        for mensagem in resposta.json()["mensagens"]
    ] == ["msg-2"]


async def test_get_conversa_retorna_a_ultima_entre_varias_respostas_da_ia():
    conversa = await _criar_conversa(
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-1",
                texto="primeira",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
            Mensagem(
                identificador_da_mensagem="msg-2",
                texto="resposta antiga",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 1),
            ),
            Mensagem(
                identificador_da_mensagem="msg-3",
                texto="resposta nova",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 2),
            ),
        ]
    )

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    assert [
        mensagem["identificador_da_mensagem"]
        for mensagem in resposta.json()["mensagens"]
    ] == ["msg-3"]


async def test_get_conversa_com_intervencao_retorna_ultima_mensagem_humana():
    conversa = await _criar_conversa(
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-1",
                texto="mensagem do lead",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
            Mensagem(
                identificador_da_mensagem="msg-2",
                texto="resposta da IA",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 1),
            ),
            Mensagem(
                identificador_da_mensagem="msg-3",
                texto="intervenção antiga",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=False,
                foi_intervencao_humana=True,
                criado_em=datetime(2026, 1, 1, 10, 2),
            ),
            Mensagem(
                identificador_da_mensagem="msg-4",
                texto="intervenção nova",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=False,
                foi_intervencao_humana=True,
                criado_em=datetime(2026, 1, 1, 10, 3),
            ),
        ],
        teve_intervencao_humana=True,
    )

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert [
        mensagem["identificador_da_mensagem"] for mensagem in dados["mensagens"]
    ] == ["msg-4"]
    assert dados["mensagens"][0]["foi_intervencao_humana"] is True


async def test_get_conversa_com_intervencao_sem_mensagem_humana_retorna_404():
    conversa = await _criar_conversa(teve_intervencao_humana=True)

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 404


async def test_get_conversa_sem_intervencao_ignora_mensagem_humana():
    conversa = await _criar_conversa(
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-1",
                texto="mensagem do lead",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
            Mensagem(
                identificador_da_mensagem="msg-2",
                texto="intervenção humana",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=False,
                foi_intervencao_humana=True,
                criado_em=datetime(2026, 1, 1, 10, 1),
            ),
            Mensagem(
                identificador_da_mensagem="msg-3",
                texto="resposta da IA",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 2),
            ),
        ]
    )

    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    assert [
        mensagem["identificador_da_mensagem"]
        for mensagem in resposta.json()["mensagens"]
    ] == ["msg-3"]


async def test_intervencao_assumir_ativa_flag(db_session):
    conversa = await _criar_conversa()

    resposta = await _post_intervencao(
        {
            "tenant_id": conversa.tenant_id,
            "telefone": str(conversa.telefone),
            "acao": "assumir",
        }
    )

    assert resposta.status_code == 200
    assert resposta.json()["teve_intervencao_humana"] is True

    atualizada = (
        await db_session.execute(select(Conversa).where(Conversa.id == conversa.id))
    ).scalar_one()
    assert atualizada.teve_intervencao_humana is True


async def test_intervencao_religar_desativa_flag(db_session):
    conversa = await _criar_conversa()
    payload = {
        "tenant_id": conversa.tenant_id,
        "telefone": str(conversa.telefone),
    }

    await _post_intervencao({**payload, "acao": "assumir"})
    resposta = await _post_intervencao({**payload, "acao": "religar"})

    assert resposta.status_code == 200
    assert resposta.json()["teve_intervencao_humana"] is False

    atualizada = (
        await db_session.execute(select(Conversa).where(Conversa.id == conversa.id))
    ).scalar_one()
    assert atualizada.teve_intervencao_humana is False


async def test_intervencao_conversa_inexistente_retorna_404():
    resposta = await _post_intervencao(
        {
            "tenant_id": "empresa-inexistente",
            "telefone": "11999999999",
            "acao": "assumir",
        }
    )

    assert resposta.status_code == 404


async def test_intervencao_acao_invalida_retorna_422():
    resposta = await _post_intervencao(
        {
            "tenant_id": "empresa-1",
            "telefone": "11999999999",
            "acao": "pausar",
        }
    )

    assert resposta.status_code == 422


async def test_religar_com_humano_espera_proxima_mensagem(enfileiramentos):
    primeira = await _post_mensagem(_payload("msg-1"))
    assert primeira.status_code == 201
    assert enfileiramentos == [("empresa-1", "11988887777", "msg-1")]

    assumir = await _post_intervencao(
        {
            "tenant_id": "empresa-1",
            "telefone": "11988887777",
            "acao": "assumir",
        }
    )
    assert assumir.status_code == 200

    segunda = await _post_mensagem(_payload("msg-2"))
    assert segunda.status_code == 201
    assert len(enfileiramentos) == 1

    humana = await _post_mensagem({**_payload("msg-humano"), "autor": "humano"})
    assert humana.status_code == 201

    religar = await _post_intervencao(
        {
            "tenant_id": "empresa-1",
            "telefone": "11988887777",
            "acao": "religar",
        }
    )
    assert religar.status_code == 200
    assert enfileiramentos == [("empresa-1", "11988887777", "msg-1")]

    terceira = await _post_mensagem(_payload("msg-3"))
    assert terceira.status_code == 201
    assert enfileiramentos[-1] == ("empresa-1", "11988887777", "msg-3")
    assert len(enfileiramentos) == 2


async def test_webhook_autor_humano_marca_intervencao(db_session, enfileiramentos):
    resposta = await _post_mensagem({**_payload("msg-humano"), "autor": "humano"})

    assert resposta.status_code == 201
    assert enfileiramentos == []

    conversa = (await db_session.execute(select(Conversa))).scalar_one()
    assert conversa.teve_intervencao_humana is True

    mensagem = (
        await db_session.execute(
            select(Mensagem).where(Mensagem.identificador_da_mensagem == "msg-humano")
        )
    ).scalar_one()
    assert mensagem.foi_intervencao_humana is True
    assert mensagem.foi_respondida_pelo_usuario is False

    dados = (await _get("/conversas/empresa-1/11988887777")).json()
    assert dados["mensagens"][0]["identificador_da_mensagem"] == "msg-humano"
    assert dados["mensagens"][0]["foi_intervencao_humana"] is True


async def test_religar_sem_pendencia_nao_enfileira(enfileiramentos):
    conversa = await _criar_conversa()
    payload = {
        "tenant_id": conversa.tenant_id,
        "telefone": str(conversa.telefone),
    }

    await _post_intervencao({**payload, "acao": "assumir"})
    resposta = await _post_intervencao({**payload, "acao": "religar"})

    assert resposta.status_code == 200
    assert enfileiramentos == []


async def test_religar_com_fila_indisponivel_retorna_503(db_session, monkeypatch):
    from dominio.regras_de_negocio.servico_ia import responder_conversa

    conversa = await _criar_conversa(
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-pendente",
                texto="mensagem pendente",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            )
        ]
    )
    payload = {
        "tenant_id": conversa.tenant_id,
        "telefone": str(conversa.telefone),
    }
    await _post_intervencao({**payload, "acao": "assumir"})

    def _falhar(*_args):
        raise RuntimeError("redis fora do ar")

    monkeypatch.setattr(responder_conversa, "criar_resposta_da_ia", _falhar)

    resposta = await _post_intervencao({**payload, "acao": "religar"})

    assert resposta.status_code == 503
    atualizada = (
        await db_session.execute(select(Conversa).where(Conversa.id == conversa.id))
    ).scalar_one()
    assert atualizada.teve_intervencao_humana is False


async def test_get_conversa_assumida_sem_mensagem_humana_retorna_404():
    conversa = await _criar_conversa()

    await _post_intervencao(
        {
            "tenant_id": conversa.tenant_id,
            "telefone": str(conversa.telefone),
            "acao": "assumir",
        }
    )
    resposta = await _get(f"/conversas/{conversa.tenant_id}/{conversa.telefone}")

    assert resposta.status_code == 404


async def test_get_conversa_inexistente_retorna_404():
    resposta = await _get("/conversas/empresa-inexistente/11999999999")

    assert resposta.status_code == 404
