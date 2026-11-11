from collections.abc import Sequence

import litellm

from config import get_settings
from dominio.regras_de_negocio.servico_ia.servico import (
    MensagemLLM,
    ProvedorLLM,
    ServicoIA,
)


class ProvedorLiteLLM(ProvedorLLM):
    """Provedor de LLM baseado no LiteLLM."""

    def __init__(
        self,
        modelo: str,
        api_base: str | None = None,
        api_key: str | None = None,
        temperatura: float = 0.7,
        timeout: float = 60.0,
    ) -> None:
        self._modelo = modelo
        self._api_base = api_base
        self._api_key = api_key
        self._temperatura = temperatura
        self._timeout = timeout

    async def gerar_resposta(self, mensagens: Sequence[MensagemLLM]) -> str:
        parametros = {
            "model": self._modelo,
            "messages": [
                {"role": mensagem.papel, "content": mensagem.conteudo}
                for mensagem in mensagens
            ],
            "temperature": self._temperatura,
            "timeout": self._timeout,
        }

        if self._api_base:
            parametros["api_base"] = self._api_base
        if self._api_key:
            parametros["api_key"] = self._api_key

        resposta = await litellm.acompletion(**parametros)

        try:
            conteudo = resposta.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ValueError("Resposta inválida do provedor de IA") from exc

        if not isinstance(conteudo, str):
            raise TypeError("Resposta inválida do provedor de IA")

        if not conteudo.strip():
            raise ValueError("Resposta vazia do provedor de IA")

        return conteudo


def construir_servico_ia() -> ServicoIA:
    settings = get_settings()
    provedor = ProvedorLiteLLM(
        modelo=settings.llm_model,
        api_base=settings.llm_api_base,
        api_key=settings.llm_api_key,
        temperatura=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
    )
    return ServicoIA(provedor)
