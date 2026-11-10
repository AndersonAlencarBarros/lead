from fastapi import APIRouter, Response, status

from dominio.objetos_de_valor.conversa import ResultadoMensagem
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.conversa import receber_mensagem
from servicos.serializadores.conversacao import (
    ConversaSerializador,
    MensagemSerializador,
)
from servicos.visualizadores.conversa import (
    buscar_conversa_por_empresa_e_telefone,
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
    },
)
async def receber_mensagem_api(mensagem: MensagemSerializador) -> Response:
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        resultado = await receber_mensagem(mensagem, uow)

    if resultado is ResultadoMensagem.DUPLICADA:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get(
    "/conversas/{tenant_id}/{telefone}",
    response_model=ConversaSerializador,
    status_code=status.HTTP_200_OK,
    tags=["Conversas"],
    summary="Buscar conversa",
    description="Retorna a conversa e suas mensagens por tenant e telefone.",
    responses={404: {"description": "Conversa não encontrada"}},
)
async def buscar_conversa_api(tenant_id: str, telefone: str):
    from exceptions import ConversaNaoEncontrada

    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa = await buscar_conversa_por_empresa_e_telefone(
            tenant_id, telefone, uow
        )

    if conversa is None:
        raise ConversaNaoEncontrada()

    return conversa
