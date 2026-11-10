from datetime import datetime

import httpx

import main
from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem, Telefone
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho


async def _criar_conversa() -> Conversa:
    conversa = Conversa(
        id=None,
        empresa_id="empresa-1",
        lead_id="lead-1",
        telefone=Telefone("11999999999"),
        mensagens=[
            Mensagem(
                id=None,
                identificador_da_mensagem="msg-2",
                conversa_id=None,
                texto="segunda",
                autor="ia",
                foi_enviada_pela_ia=True,
                foi_enviada_pelo_humano=False,
                criado_em=datetime(2026, 1, 1, 10, 5),
            ),
            Mensagem(
                id=None,
                identificador_da_mensagem="msg-1",
                conversa_id=None,
                texto="primeira",
                autor="lead",
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
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        return await client.get(path)


async def test_get_conversa_retorna_mensagens_associadas():
    conversa = await _criar_conversa()

    resposta = await _get(f"/conversas/{conversa.empresa_id}/{conversa.telefone}")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["id"] == conversa.id
    assert dados["lead_id"] == "lead-1"
    assert [
        mensagem["identificador_da_mensagem"] for mensagem in dados["mensagens"]
    ] == ["msg-1", "msg-2"]


async def test_get_conversa_inexistente_retorna_404():
    resposta = await _get("/conversas/empresa-inexistente/11999999999")

    assert resposta.status_code == 404
