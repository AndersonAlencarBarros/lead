from types import SimpleNamespace

import litellm
import pytest

from dominio.regras_de_negocio.servico_ia import ProvedorLiteLLM


def _resposta(conteudo: str) -> SimpleNamespace:
    mensagem = SimpleNamespace(content=conteudo, tool_calls=())
    usage = SimpleNamespace(prompt_tokens=2, completion_tokens=3)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=mensagem)],
        usage=usage,
        model="ollama/qwen2.5:7b",
    )


def _ferramentas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "consultar_agenda",
                "description": "Retorna horários livres.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        }
    ]


async def test_gerar_resposta_envia_parametros_ao_litellm(monkeypatch):
    capturado: dict = {}

    async def completion_falso(**kwargs):
        capturado.update(kwargs)
        return _resposta("olá")

    monkeypatch.setattr(litellm, "acompletion", completion_falso)
    provider = ProvedorLiteLLM(
        modelo="ollama/qwen2.5:7b",
        api_base="http://localhost:11434",
        temperatura=0.2,
        timeout=12,
    )
    ferramentas = _ferramentas()

    resposta = await provider.gerar_resposta(
        [{"role": "user", "content": "oi"}],
        ferramentas,
    )

    assert resposta.conteudo == "olá"
    assert resposta.tokens_entrada == 2
    assert resposta.tokens_saida == 3
    assert capturado["model"] == "ollama/qwen2.5:7b"
    assert capturado["api_base"] == "http://localhost:11434"
    assert capturado["temperature"] == 0.2
    assert capturado["timeout"] == 12
    assert capturado["messages"] == [{"role": "user", "content": "oi"}]
    assert capturado["tools"] == ferramentas
    assert capturado["tool_choice"] == "auto"
    assert "api_key" not in capturado


async def test_gerar_resposta_extrai_tool_call(monkeypatch):
    chamada = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(
            name="consultar_agenda",
            arguments="{}",
        ),
    )
    mensagem = SimpleNamespace(content=None, tool_calls=[chamada])
    resposta_litellm = SimpleNamespace(
        choices=[SimpleNamespace(message=mensagem)],
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        model="fake",
    )

    async def completion_falso(**kwargs):
        return resposta_litellm

    monkeypatch.setattr(litellm, "acompletion", completion_falso)
    provider = ProvedorLiteLLM(modelo="fake")

    resposta = await provider.gerar_resposta(
        [{"role": "user", "content": "oi"}],
        _ferramentas(),
    )

    assert resposta.conteudo is None
    assert resposta.chamadas[0].nome == "consultar_agenda"
    assert resposta.chamadas[0].argumentos == {}


async def test_gerar_resposta_rejeita_conteudo_vazio(monkeypatch):
    async def completion_falso(**kwargs):
        return _resposta("")

    monkeypatch.setattr(litellm, "acompletion", completion_falso)
    provider = ProvedorLiteLLM(modelo="ollama/qwen2.5:7b")

    with pytest.raises(ValueError):
        await provider.gerar_resposta(
            [{"role": "user", "content": "oi"}],
            [],
        )
