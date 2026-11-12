import json
import logging
from typing import Any

import litellm

from config import get_settings
from dominio.regras_de_negocio.servico_ia.servico import (
    ChamadaFerramenta,
    ProvedorLLM,
    RespostaLLM,
    ServicoIA,
)

logger = logging.getLogger(__name__)


class ProvedorLiteLLM(ProvedorLLM):
    """Provedor de LLM baseado no LiteLLM, com tool calling."""

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

    async def gerar_resposta(
        self,
        mensagens: list[dict[str, Any]],
        ferramentas: list[dict[str, Any]],
    ) -> RespostaLLM:
        parametros: dict[str, Any] = {
            "model": self._modelo,
            "messages": mensagens,
            "temperature": self._temperatura,
            "timeout": self._timeout,
        }

        if ferramentas:
            parametros["tools"] = ferramentas
            parametros["tool_choice"] = "auto"

        if self._api_base:
            parametros["api_base"] = self._api_base
        if self._api_key:
            parametros["api_key"] = self._api_key

        resposta = await litellm.acompletion(**parametros)

        try:
            mensagem = resposta.choices[0].message
        except (AttributeError, IndexError, TypeError) as exc:
            raise ValueError("Resposta inválida do provedor de IA") from exc

        conteudo = getattr(mensagem, "content", None)
        if isinstance(conteudo, dict):
            conteudo = json.dumps(conteudo, ensure_ascii=False)
        if conteudo is not None and not isinstance(conteudo, str):
            raise TypeError("Resposta inválida do provedor de IA")

        chamadas = tuple(
            self._chamada(chamada)
            for chamada in (getattr(mensagem, "tool_calls", None) or ())
        )

        if not (conteudo or "").strip() and not chamadas:
            raise ValueError("Resposta vazia do provedor de IA")

        if not chamadas and (conteudo or "").lstrip().startswith(("{", "[")):
            logger.warning(
                "provider_devolveu_json_no_conteudo",
                extra={
                    "modelo": str(
                        getattr(resposta, "model", self._modelo) or self._modelo
                    ),
                    "conteudo": conteudo[:300],
                },
            )

        usage = getattr(resposta, "usage", None)
        tokens_entrada = self._token(usage, "prompt_tokens")
        tokens_saida = self._token(usage, "completion_tokens")

        return RespostaLLM(
            conteudo=conteudo,
            chamadas=chamadas,
            modelo=str(getattr(resposta, "model", self._modelo) or self._modelo),
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
        )

    @staticmethod
    def _chamada(chamada: Any) -> ChamadaFerramenta:
        argumentos = chamada.function.arguments or "{}"
        if isinstance(argumentos, str):
            argumentos = json.loads(argumentos)
        return ChamadaFerramenta(
            id=chamada.id,
            nome=chamada.function.name,
            argumentos=argumentos,
        )

    @staticmethod
    def _token(usage: Any, campo: str) -> int:
        if usage is None:
            return 0
        if isinstance(usage, dict):
            return int(usage.get(campo) or 0)
        return int(getattr(usage, campo, 0) or 0)


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
