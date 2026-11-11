from collections.abc import Sequence
from datetime import datetime

import pytest

from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.conversa import Mensagem
from dominio.objetos_de_valor.empresa import (
    ConfiguracaoIA,
    Intervalo,
    StatusEmpresa,
    TomDaIA,
)
from dominio.regras_de_negocio.servico_ia import (
    MensagemLLM,
    ProvedorLLM,
    ServicoIA,
)
from exceptions import FalhaAoConsultarIA


class ProviderFalso(ProvedorLLM):
    def __init__(self, texto: str = "resposta da IA") -> None:
        self.texto = texto
        self.mensagens: Sequence[MensagemLLM] | None = None

    async def gerar_resposta(self, mensagens: Sequence[MensagemLLM]) -> str:
        self.mensagens = mensagens
        return self.texto


def _empresa() -> Empresa:
    return Empresa(
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
        regras_gerais=["Seja breve"],
        cidades_atendidas=["São Paulo"],
        estagios=["novo"],
    )


def _conversa() -> Conversa:
    return Conversa(
        tenant_id="empresa-1",
        telefone="11988887777",
        mensagens=[
            Mensagem(
                identificador_da_mensagem="msg-1",
                texto="Olá",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime(2026, 1, 1, 10, 0),
            ),
            Mensagem(
                identificador_da_mensagem="msg-2",
                texto="Olá! Como posso ajudar?",
                foi_gerada_pela_ia=True,
                foi_respondida_pelo_usuario=False,
                criado_em=datetime(2026, 1, 1, 10, 1),
            ),
        ],
    )


async def test_responder_monta_sistema_e_historico():
    provider = ProviderFalso()
    service = ServicoIA(provider)

    resposta = await service.responder(_conversa().mensagens, _empresa())

    assert resposta == "resposta da IA"
    assert provider.mensagens is not None
    assert [mensagem.papel for mensagem in provider.mensagens] == [
        "system",
        "user",
        "assistant",
    ]
    assert "Ana" in provider.mensagens[0].conteudo
    assert "informal" in provider.mensagens[0].conteudo
    assert "Seja breve" in provider.mensagens[0].conteudo
    assert "São Paulo" in provider.mensagens[0].conteudo
    assert provider.mensagens[1].conteudo == "Olá"
    assert provider.mensagens[2].conteudo == "Olá! Como posso ajudar?"


async def test_falha_do_provider_vira_erro_de_ia():
    class ProviderComFalha(ProvedorLLM):
        async def gerar_resposta(self, mensagens: Sequence[MensagemLLM]) -> str:
            raise RuntimeError("falha")

    service = ServicoIA(ProviderComFalha())

    with pytest.raises(FalhaAoConsultarIA):
        await service.responder(_conversa().mensagens, _empresa())


async def test_resposta_vazia_vira_erro_de_ia():
    service = ServicoIA(ProviderFalso(texto="   "))

    with pytest.raises(FalhaAoConsultarIA):
        await service.responder(_conversa().mensagens, _empresa())
