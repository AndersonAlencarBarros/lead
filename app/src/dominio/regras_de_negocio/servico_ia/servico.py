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
        mensagens = list(mensagens)
        primeiro_turno = not any(
            mensagem.foi_gerada_pela_ia or mensagem.foi_intervencao_humana
            for mensagem in mensagens
        )
        teve_intervencao_humana = any(
            mensagem.foi_intervencao_humana for mensagem in mensagens
        )
        contexto = [
            {
                "role": "system",
                "content": self._prompt_sistema(
                    empresa,
                    lead,
                    primeiro_turno=primeiro_turno,
                    teve_intervencao_humana=teve_intervencao_humana,
                ),
            },
            *[self._mensagem_para_contexto(mensagem) for mensagem in mensagens],
        ]

        try:
            return await self._executar_turno(
                contexto,
                ferramentas,
                executar_ferramenta,
                lead,
            )
        except FalhaAoConsultarIA:
            raise
        except Exception as exc:
            raise FalhaAoConsultarIA() from exc

    @staticmethod
    def _mensagem_para_contexto(mensagem: Mensagem) -> dict[str, str]:
        if mensagem.foi_intervencao_humana:
            return {
                "role": "assistant",
                "content": f"[Atendente humano]: {mensagem.texto}",
            }
        return {
            "role": "assistant" if mensagem.foi_gerada_pela_ia else "user",
            "content": mensagem.texto,
        }

    async def _executar_turno(
        self,
        contexto: list[dict[str, Any]],
        ferramentas: list[dict[str, Any]],
        executar_ferramenta: ExecutarFerramenta | None,
        lead: Lead | None,
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

            texto_invalido = not self._texto_final_valido(texto)
            if not texto_invalido:
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

            contexto.append({"role": "assistant", "content": texto})
            contexto.append(
                {
                    "role": "system",
                    "content": (
                        "Não responda com JSON, nome de ferramenta ou argumentos. "
                        "Use function calling e escreva texto natural para o lead."
                    ),
                }
            )

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
                    "content": self._serializar(
                        self._resultado_para_contexto(resultado)
                    ),
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

    def _prompt_sistema(
        self,
        empresa: Empresa,
        lead: Lead | None,
        primeiro_turno: bool,
        teve_intervencao_humana: bool,
    ) -> str:
        playbook = empresa.playbook
        configuracao = empresa.configuracao_ia
        linhas = [
            (
                f"Você é {configuracao.nome_assistente}, assistente de "
                f"atendimento da empresa {empresa.nome}."
            ),
            f"Tom de voz: {configuracao.tom.value}.",
            f"Objetivo: {playbook.objetivo}.",
            """
            REGRAS DE CONVERSAÇÃO:
            1. Faça apenas UMA pergunta por mensagem.
            2. Nunca solicite várias informações simultaneamente.
            3. Aguarde a resposta do usuário antes de perguntar o próximo campo.
            4. Utilize as informações já fornecidas anteriormente.
            5. Não pergunte novamente informações que já foram respondidas.
            6. Seja natural e mantenha uma conversa amigável.
            7. Não apresente opções de agendamento enquanto a
               qualificação não estiver completa.
            8. Execute ferramentas somente quando houver informações
               suficientes para a operação.
            9. Não considere uma informação como preenchida sem
               confirmação do usuário.

            IMPORTANTE:
            Após receber cada resposta, verifique qual é a
            próxima informação pendente e pergunte somente ela.
           """,
        ]

        if primeiro_turno:
            linhas.append(
                "Esta é a primeira mensagem da conversa. Cumprimente o lead "
                "e faça no máximo a primeira pergunta de qualificação."
            )
        else:
            linhas.append(
                "Continue a conversa a partir da última mensagem. Faça no "
                "máximo uma pergunta por mensagem."
            )

        if teve_intervencao_humana:
            linhas.extend(
                [
                    (
                        "Mensagens com o prefixo [Atendente humano] foram "
                        "escritas por uma pessoa da equipe, não por você."
                    ),
                    (
                        "Continue a partir do que o atendente humano já "
                        "respondeu. Não repita nem contradiga a resposta dele."
                    ),
                    ("Não pergunte dado que o lead ou o atendente humano já informou."),
                ]
            )

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

        if lead is not None:
            linhas.append(f"Estágio atual do lead: {lead.estagio or 'não definido'}")

        linhas.extend(
            [
                (
                    "Só ofereça horário depois de concluir as perguntas de "
                    "qualificação ou se o lead pedir explicitamente para agendar."
                ),
                (
                    "Consulte a agenda antes de oferecer horário e nunca "
                    "ofereça horário sem consultar_agenda."
                ),
                (
                    "Execute mover_estagio apenas quando houver mudança real "
                    "de estágio; não faça isso em saudação."
                ),
                (
                    "Mova para Qualificado quando o lead cumprir os critérios "
                    "de qualificação; para Desqualificado quando não cumprir; "
                    "para Agendado após marcar a agenda com sucesso."
                ),
                (
                    "Não marque o lead como Qualificado antes de cumprir os "
                    "critérios de qualificação."
                ),
                (
                    "Nunca mencione ao lead estágio, qualificação, IDs, nomes "
                    "de ferramentas ou dados internos."
                ),
                (
                    "Não diga que o lead foi qualificado, desqualificado ou "
                    "movido de estágio."
                ),
                (
                    "Não repita o perfil completo do lead; confirme apenas o "
                    "necessário. Informe agendamento apenas com data e hora "
                    "legíveis, sem formato técnico."
                ),
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
    def _resultado_para_contexto(resultado: dict[str, Any]) -> dict[str, Any]:
        return {
            chave: valor
            for chave, valor in resultado.items()
            if chave != "agendamento_id"
        }

    @staticmethod
    def _serializar(resultado: dict[str, Any]) -> str:
        return json.dumps(resultado, ensure_ascii=False, default=str)
