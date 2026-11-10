from fastapi import APIRouter, status

from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.mensagem import receber_mensagem
from servicos.serializadores.conversacao import (
    ConversaSerializador,
    MensagemSerializador,
)
from servicos.visualizadores.conversa import (
    buscar_conversa_por_empresa_e_telefone,
)

router = APIRouter()

@router.post("/webhook/mensagem", response_model=MensagemSerializador, status_code=status.HTTP_200_OK)
async def receber_mensagem_api(mensagem: MensagemSerializador):
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        return await receber_mensagem(mensagem, uow)


@router.get(
    "/conversas/{empresa_id}/{telefone}",
    response_model=ConversaSerializador,
    status_code=status.HTTP_200_OK,
)
async def buscar_conversa_api(empresa_id: str, telefone: str):
    from exceptions import ConversaNaoEncontrada

    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa = await buscar_conversa_por_empresa_e_telefone(
            empresa_id, telefone, uow
        )

    if conversa is None:
        raise ConversaNaoEncontrada()

    return conversa
