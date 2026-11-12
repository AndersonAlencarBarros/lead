import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from dominio.agregados.empresa import Empresa
from dominio.agregados.lead import Lead
from dominio.objetos_de_valor.conversa import Mensagem
from dominio.regras_de_negocio.servico_ia.ferramentas import (
    construir_ferramentas,
)
from exceptions import FalhaAoConsultarIA

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChamadaFerramenta:
    id: str
    nome: str
    argumentos: dict[str, Any]


@dataclass(frozen=True)
class RespostaLLM:
    conteudo: str | None
    chamadas: tuple[ChamadaFerramenta, ...]
    modelo: str
    tokens_entrada: int
    tokens_saida: int


@dataclass(frozen=True)
class ResultadoTurno:
    texto: str
    acoes: list[dict[str, Any]]
    modelo: str
    tokens_entrada: int
    tokens_saida: int
    iteracoes: int


ExecutarFerramenta = Callable[[ChamadaFerramenta], Awaitable[dict[str, Any]]]


class ProvedorLLM(ABC):
    """Contrato mínimo para provedores de LLM com tool calling."""

    @abstractmethod
    async def gerar_resposta(
        self,
        mensagens: list[dict[str, Any]],
        ferramentas: list[dict[str, Any]],
    ) -> RespostaLLM:
        """Gera uma resposta e eventuais chamadas de ferramenta."""
        raise NotImplementedError


class ServicoIA:
    """Monta o contexto, conduz o loop de ferramentas e valida o turno."""

    def __init__(
        self,
        provedor: ProvedorLLM,
        max_iteracoes: int = 6,
        max_correcoes: int = 2,
    ) -> None:
        self._provedor = provedor
        self._max_iteracoes = max_iteracoes
        self._max_correcoes = max_correcoes

    async def responder(
        self,
        mensagens: Sequence[Mensagem],
        empresa: Empresa,
        lead: Lead | None = None,
        executar_ferramenta: ExecutarFerramenta | None = None,
    ) -> ResultadoTurno:
        ferramentas = (
            construir_ferramentas(empresa) if executar_ferramenta is not None else []
        )
        contexto = [
            {"role": "system", "content": self._prompt_sistema(empresa, lead)},
            *[
                {
                    "role": (
                        "assistant"
                        if mensagem.foi_gerada_pela_ia
                        or mensagem.foi_intervencao_humana
                        else "user"
                    ),
                    "content": mensagem.texto,
                }
                for mensagem in mensagens
            ],
        ]

        try:
            return await self._executar_turno(
                contexto,
                ferramentas,
                executar_ferramenta,
            )
        except FalhaAoConsultarIA:
            raise
        except Exception as exc:
            raise FalhaAoConsultarIA() from exc

    async def _executar_turno(
        self,
        contexto: list[dict[str, Any]],
        ferramentas: list[dict[str, Any]],
        executar_ferramenta: ExecutarFerramenta | None,
    ) -> ResultadoTurno:
        acoes: list[dict[str, Any]] = []
        correcoes = 0
        tokens_entrada = 0
        tokens_saida = 0
        modelo = ""

        for iteracao in range(1, self._max_iteracoes + 1):
            resposta = await self._provedor.gerar_resposta(
                contexto,
                ferramentas,
            )
            modelo = resposta.modelo
            tokens_entrada += resposta.tokens_entrada
            tokens_saida += resposta.tokens_saida

            if resposta.chamadas:
                if executar_ferramenta is None:
                    raise FalhaAoConsultarIA()

                await self._executar_chamadas(
                    contexto,
                    resposta.chamadas,
                    resposta.conteudo,
                    executar_ferramenta,
                    acoes,
                )
                continue

            texto = (resposta.conteudo or "").strip()
            if not texto:
                raise FalhaAoConsultarIA()

            if executar_ferramenta is None:
                if not self._texto_final_valido(texto):
                    raise FalhaAoConsultarIA()
                return self._resultado(
                    texto,
                    acoes,
                    modelo,
                    tokens_entrada,
                    tokens_saida,
                    iteracao,
                )

            chamada_em_texto = self._chamada_do_texto(texto, ferramentas)
            if chamada_em_texto is not None:
                logger.warning(
                    "tool_call_recuperada_do_texto",
                    extra={
                        "modelo": modelo,
                        "ferramenta": chamada_em_texto.nome,
                        "texto": texto[:300],
                    },
                )
                await self._executar_chamadas(
                    contexto,
                    (chamada_em_texto,),
                    None,
                    executar_ferramenta,
                    acoes,
                )
                continue

            falta_invariante = not self._tem_tag_e_estagio(acoes)
            texto_invalido = not self._texto_final_valido(texto)

            if not falta_invariante and not texto_invalido:
                return self._resultado(
                    texto,
                    acoes,
                    modelo,
                    tokens_entrada,
                    tokens_saida,
                    iteracao,
                )

            correcoes += 1
            if correcoes > self._max_correcoes:
                break

            instrucoes = []
            if falta_invariante:
                instrucoes.append(
                    "Você encerrou sem executar adicionar_tag e mover_estagio."
                )
            if texto_invalido:
                instrucoes.append(
                    "Não responda com JSON, nome de ferramenta ou argumentos. "
                    "Use function calling e escreva texto natural para o lead."
                )

            contexto.append({"role": "assistant", "content": texto})
            contexto.append({"role": "system", "content": " ".join(instrucoes)})

        raise FalhaAoConsultarIA()

    async def _executar_chamadas(
        self,
        contexto: list[dict[str, Any]],
        chamadas: Sequence[ChamadaFerramenta],
        conteudo: str | None,
        executar_ferramenta: ExecutarFerramenta,
        acoes: list[dict[str, Any]],
    ) -> None:
        contexto.append(
            {
                "role": "assistant",
                "content": conteudo,
                "tool_calls": [
                    {
                        "id": chamada.id,
                        "type": "function",
                        "function": {
                            "name": chamada.nome,
                            "arguments": json.dumps(
                                chamada.argumentos,
                                ensure_ascii=False,
                            ),
                        },
                    }
                    for chamada in chamadas
                ],
            }
        )

        for chamada in chamadas:
            resultado = await executar_ferramenta(chamada)
            acoes.append(
                {
                    "ferramenta": chamada.nome,
                    "argumentos": chamada.argumentos,
                    "resultado": resultado,
                    "sucesso": not resultado.get("erro"),
                }
            )
            contexto.append(
                {
                    "role": "tool",
                    "tool_call_id": chamada.id,
                    "content": self._serializar(resultado),
                }
            )

    @staticmethod
    def _resultado(
        texto: str,
        acoes: list[dict[str, Any]],
        modelo: str,
        tokens_entrada: int,
        tokens_saida: int,
        iteracoes: int,
    ) -> ResultadoTurno:
        return ResultadoTurno(
            texto=texto,
            acoes=acoes,
            modelo=modelo,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            iteracoes=iteracoes,
        )

    @staticmethod
    def _tem_tag_e_estagio(acoes: list[dict[str, Any]]) -> bool:
        nomes = {acao["ferramenta"] for acao in acoes if acao["sucesso"]}
        return "adicionar_tag" in nomes and "mover_estagio" in nomes

    @staticmethod
    def _texto_final_valido(texto: str) -> bool:
        limpo = texto.strip()
        return bool(limpo) and not limpo.startswith(("{", "[", "```"))

    @staticmethod
    def _chamada_do_texto(
        texto: str,
        ferramentas: list[dict[str, Any]],
    ) -> ChamadaFerramenta | None:
        try:
            dados = json.loads(texto.strip())
        except json.JSONDecodeError:
            return None

        if not isinstance(dados, dict):
            return None

        nome = dados.get("name")
        nomes = {ferramenta["function"]["name"] for ferramenta in ferramentas}
        if nome not in nomes:
            return None

        argumentos = dados.get("arguments") or {}
        if not isinstance(argumentos, dict):
            return None

        return ChamadaFerramenta(
            id=f"texto-{uuid4()}",
            nome=nome,
            argumentos=argumentos,
        )

    def _prompt_sistema(self, empresa: Empresa, lead: Lead | None) -> str:
        playbook = empresa.playbook
        configuracao = empresa.configuracao_ia
        linhas = [
            (
                f"Você é {configuracao.nome_assistente}, assistente de "
                f"atendimento da empresa {empresa.nome}."
            ),
            f"Tom de voz: {configuracao.tom.value}.",
            f"Objetivo: {playbook.objetivo}.",
        ]

        if configuracao.pode_dizer_que_e_ia:
            linhas.append("Você pode informar que é uma IA quando perguntado.")
        else:
            linhas.append("Não informe que você é uma IA.")

        if playbook.perguntas:
            linhas.append("Perguntas de qualificação:")
            linhas.extend(f"- {pergunta}" for pergunta in playbook.perguntas)

        if playbook.criterios_de_qualificacao:
            linhas.append("Critérios de decisão:")
            linhas.extend(
                f"- {criterio}" for criterio in playbook.criterios_de_qualificacao
            )

        regras = [
            *[str(regra) for regra in empresa.regras_gerais],
            *playbook.regras,
        ]
        if regras:
            linhas.append("Regras gerais:")
            linhas.extend(f"- {regra}" for regra in regras)

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

        linhas.append("Campos permitidos na ficha:")
        linhas.extend(f"- {campo.nome}: {campo.descricao}" for campo in playbook.campos)

        if lead is not None:
            linhas.extend(
                [
                    f"Ficha atual do lead: {lead.ficha_como_json()}",
                    f"Tags atuais do lead: {lead.tags}",
                    f"Estágio atual do lead: {lead.estagio}",
                ]
            )

        linhas.extend(
            [
                (
                    "Grave na ficha apenas dado dito pelo lead, com evidência "
                    "literal da mensagem."
                ),
                "Não pergunte dado que já está na ficha.",
                "Consulte a agenda antes de oferecer horário.",
                "Antes de responder, execute adicionar_tag e mover_estagio.",
                (
                    "Nunca escreva JSON, nome de ferramenta ou argumentos no "
                    "corpo da mensagem."
                ),
                (
                    "Se precisar consultar a agenda, chame consultar_agenda; "
                    'não escreva {"name": "consultar_agenda"}.'
                ),
                "Responda apenas com a mensagem a ser enviada ao lead, em português.",
            ]
        )
        return "\n".join(linhas)

    @staticmethod
    def _serializar(resultado: dict[str, Any]) -> str:
        return json.dumps(resultado, ensure_ascii=False, default=str)
