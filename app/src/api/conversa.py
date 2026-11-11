from fastapi import APIRouter, Response, status

from dominio.objetos_de_valor.conversa import ResultadoMensagem
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.conversa import (
    alterar_intervencao,
    receber_mensagem,
    responder_ultima_mensagem_da_conversa,
)
from servicos.serializadores.conversacao import (
    ConversaSerializador,
    IntervencaoResposta,
    IntervencaoSerializador,
    MensagemResposta,
    MensagemSerializador,
)

router = APIRouter()


@router.post(
    "/webhook/mensagem",
    status_code=status.HTTP_201_CREATED,
    tags=["Webhook"],
    summary="Receber mensagem",
    description=("Persiste a mensagem; duplicatas são ignoradas de forma idempotente."),
    responses={
        201: {"description": "Mensagem processada"},
        204: {"description": "Mensagem duplicada ignorada"},
        503: {"description": "Fila de processamento indisponível"},
    },
)
async def receber_mensagem_api(mensagem: MensagemSerializador) -> Response:
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        resultado = await receber_mensagem(mensagem, uow)

    if resultado is ResultadoMensagem.DUPLICADA:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return Response(status_code=status.HTTP_201_CREATED)


@router.post(
    "/intervencao",
    response_model=IntervencaoResposta,
    status_code=status.HTTP_200_OK,
    tags=["Conversas"],
    summary="Alterar intervenção humana",
    description="Assume a conversa ou devolve o atendimento para a IA.",
    responses={404: {"description": "Conversa não encontrada"}},
)
async def alterar_intervencao_api(payload: IntervencaoSerializador):
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa = await alterar_intervencao(payload, uow)

    return IntervencaoResposta(
        tenant_id=conversa.tenant_id,
        telefone=str(conversa.telefone),
        teve_intervencao_humana=conversa.teve_intervencao_humana,
    )


@router.get(
    "/conversas/{tenant_id}/{telefone}",
    response_model=ConversaSerializador,
    status_code=status.HTTP_200_OK,
    tags=["Conversas"],
    summary="Buscar última mensagem",
    description=(
        "Retorna a conversa e a última mensagem gerada pela IA. Durante "
        "intervenção humana, retorna a última mensagem da intervenção."
    ),
    responses={
        404: {
            "description": (
                "Conversa, resposta da IA ou intervenção humana não encontrada"
            )
        }
    },
)
async def responder_conversa_api(tenant_id: str, telefone: str):
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa, mensagem = await responder_ultima_mensagem_da_conversa(
            tenant_id,
            telefone,
            uow,
        )

    return ConversaSerializador(
        id=conversa.id,
        tenant_id=conversa.tenant_id,
        lead_id=conversa.lead_id,
        teve_intervencao_humana=conversa.teve_intervencao_humana,
        criado_em=conversa.criado_em,
        mensagens=[MensagemResposta.model_validate(mensagem)],
    )
