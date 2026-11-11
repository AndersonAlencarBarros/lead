from types import SimpleNamespace

import litellm
import pytest

from dominio.regras_de_negocio.servico_ia import MensagemLLM, ProvedorLiteLLM


def _resposta(conteudo: str) -> SimpleNamespace:
    mensagem = SimpleNamespace(content=conteudo)
    return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)])


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

    resposta = await provider.gerar_resposta([MensagemLLM("user", "oi")])

    assert resposta == "olá"
    assert capturado["model"] == "ollama/qwen2.5:7b"
    assert capturado["api_base"] == "http://localhost:11434"
    assert capturado["temperature"] == 0.2
    assert capturado["timeout"] == 12
    assert capturado["messages"] == [{"role": "user", "content": "oi"}]
    assert "api_key" not in capturado


async def test_gerar_resposta_rejeita_conteudo_vazio(monkeypatch):
    async def completion_falso(**kwargs):
        return _resposta("")

    monkeypatch.setattr(litellm, "acompletion", completion_falso)
    provider = ProvedorLiteLLM(modelo="ollama/qwen2.5:7b")

    with pytest.raises(ValueError):
        await provider.gerar_resposta([MensagemLLM("user", "oi")])
