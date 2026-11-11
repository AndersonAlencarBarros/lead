from datetime import datetime

import httpx
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
    ProvedorLiteLLM,
    ServicoIA,
)
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.conversa import responder_conversa

MODELO = "ollama/qwen2.5-coder:7b"
API_BASE = "http://localhost:11434"


@pytest.fixture(scope="module", autouse=True)
def ollama_disponivel():
    try:
        resposta = httpx.get(f"{API_BASE}/api/tags", timeout=5)
        resposta.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"Ollama indisponível em {API_BASE}: {exc}")

    modelos = {modelo["name"] for modelo in resposta.json().get("models", [])}
    tag = MODELO.removeprefix("ollama/").removeprefix("ollama_chat/")
    if tag not in modelos:
        pytest.skip(f"Modelo {tag} ausente; rode: ollama pull {tag}")


def _provider() -> ProvedorLiteLLM:
    return ProvedorLiteLLM(
        modelo=MODELO,
        api_base=API_BASE,
        temperatura=0,
        timeout=120,
    )


def _empresa() -> Empresa:
    agora = datetime.now()
    return Empresa(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status=StatusEmpresa.ATIVA,
        telefone_notificacao="11999999999",
        configuracao_ia=ConfiguracaoIA(
            tom=TomDaIA.FORMAL,
            pode_dizer_que_e_ia=True,
            nome_assistente="Ana",
            horario_atendimento_ia=Intervalo(
                horario_inicio=agora.replace(hour=0, minute=0, second=0, microsecond=0),
                horario_fim=agora.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ),
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
                texto="Olá, vocês atendem em São Paulo?",
                foi_gerada_pela_ia=False,
                foi_respondida_pelo_usuario=True,
                criado_em=datetime.now(),
            )
        ],
    )


async def _criar_dados() -> None:
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        await uow.dominio.salvar(_empresa())
        await uow.commit()

    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        await uow.dominio.salvar(_conversa())
        await uow.commit()


async def _buscar_conversa() -> Conversa | None:
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        return await uow.leitura.buscar_por_empresa_e_telefone(
            "empresa-1", "11988887777"
        )


async def test_litellm_provider_chama_ollama_real():
    provider = _provider()

    resposta = await provider.gerar_resposta(
        [
            MensagemLLM(
                "user",
                "Responda apenas com uma saudação curta em português.",
            )
        ]
    )

    assert isinstance(resposta, str)
    assert resposta.strip()


async def test_ai_service_responde_com_ollama_real():
    service = ServicoIA(_provider())

    resposta = await service.responder(_conversa().mensagens, _empresa())

    assert resposta.strip()


async def test_responder_conversa_persiste_resposta_com_ollama_real():
    await _criar_dados()
    service = ServicoIA(_provider())

    gerou = await responder_conversa(
        "empresa-1",
        "11988887777",
        "msg-1",
        service,
    )

    assert gerou is True
    conversa = await _buscar_conversa()
    assert conversa is not None
    respostas = [
        mensagem for mensagem in conversa.mensagens if mensagem.foi_gerada_pela_ia
    ]
    assert len(respostas) == 1
    resposta = respostas[0]
    assert resposta.texto.strip()
    assert resposta.foi_respondida_pelo_usuario is False
    assert resposta.identificador_da_mensagem.startswith("ia:")

    gerou_novamente = await responder_conversa(
        "empresa-1",
        "11988887777",
        "msg-1",
        service,
    )

    assert gerou_novamente is False
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert (
        len(
            [mensagem for mensagem in conversa.mensagens if mensagem.foi_gerada_pela_ia]
        )
        == 1
    )
