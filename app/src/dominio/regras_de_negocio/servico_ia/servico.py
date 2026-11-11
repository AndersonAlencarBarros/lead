from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.conversa import Mensagem
from exceptions import FalhaAoConsultarIA

PapelMensagem = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class MensagemLLM:
    papel: PapelMensagem
    conteudo: str


class ProvedorLLM(ABC):
    """
    Contrato para provedores de LLM.
    Qualquer outro provedor LLM deve implementar essa classe
    e método abstrato.
    """

    @abstractmethod
    async def gerar_resposta(self, mensagens: Sequence[MensagemLLM]) -> str:
        """Gera uma resposta a partir das mensagens de contexto."""
        raise NotImplementedError


class ServicoIA:
    """Monta o contexto da conversa e delega a geração ao provedor de LLM."""

    def __init__(self, provedor: ProvedorLLM) -> None:
        self._provedor = provedor

    async def responder(self, mensagens: Sequence[Mensagem], empresa: Empresa) -> str:
        contexto = [
            MensagemLLM("system", self._prompt_sistema(empresa)),
            *[self._mensagem_de_contexto(mensagem) for mensagem in mensagens],
        ]

        try:
            resposta = await self._provedor.gerar_resposta(contexto)
        except FalhaAoConsultarIA:
            raise
        except Exception as exc:
            raise FalhaAoConsultarIA() from exc

        texto = resposta.strip()
        if not texto:
            raise FalhaAoConsultarIA()

        return texto

    def _prompt_sistema(self, empresa: Empresa) -> str:
        configuracao = empresa.configuracao_ia
        linhas = [
            (
                f"Você é {configuracao.nome_assistente}, assistente de "
                f"atendimento da empresa {empresa.nome}."
            ),
            f"Tom de voz: {configuracao.tom.value}.",
        ]

        if configuracao.pode_dizer_que_e_ia:
            linhas.append("Você pode informar que é uma IA quando perguntado.")
        else:
            linhas.append("Não informe que você é uma IA.")

        if empresa.regras_gerais:
            linhas.append("Regras gerais:")
            linhas.extend(f"- {regra}" for regra in empresa.regras_gerais)

        if empresa.cidades_atendidas:
            linhas.append(
                "Cidades atendidas: "
                + ", ".join(str(cidade) for cidade in empresa.cidades_atendidas)
            )

        if empresa.estagios:
            linhas.append(
                "Estágios do atendimento: "
                + ", ".join(str(estagio) for estagio in empresa.estagios)
            )

        linhas.append(
            "Responda apenas com a mensagem a ser enviada ao lead, em português."
        )
        return "\n".join(linhas)

    def _mensagem_de_contexto(self, mensagem: Mensagem) -> MensagemLLM:
        papel = (
            "assistant"
            if mensagem.foi_gerada_pela_ia or mensagem.foi_intervencao_humana
            else "user"
        )
        return MensagemLLM(
            papel=papel,
            conteudo=mensagem.texto,
        )
