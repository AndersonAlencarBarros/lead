from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import wraps

from sqlalchemy.exc import IntegrityError

from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem, ResultadoMensagem
from infraestrutura import UnidadeDeTrabalho
from repositorio.conversa import ConversaDominioRepositorio, ConversaLeituraRepositorio
from servicos.serializadores.conversacao import MensagemSerializador


def adicionar_tag(): ...


def mover_estagio(): ...


def atualizar_ficha(db, lead_id: int, campo: str, valor: str):
    campos_permitidos = {
        "nome",
        "cidade",
        "tipo_imovel",
        "situacao_imovel",
        "valor_conta",
        "forma_pagamento",
    }

    if campo not in campos_permitidos:
        raise ValueError("Campo não permitido")

    db.execute(f"UPDATE leads SET {campo} = ? WHERE id = ?", (valor, lead_id))

    db.commit()

    return {"sucesso": True, "campo": campo, "valor": valor}


def notificar_equipe(): ...


def transferir_humano(): ...


def consultar_agenda(): ...


def marcar_agenda(): ...


def idempotente_em_conflito(
    fn: Callable[..., Awaitable[ResultadoMensagem]],
) -> Callable[..., Awaitable[ResultadoMensagem]]:
    """Repete uma vez em conflito de concorrência e trata duplicidade como sucesso."""

    @wraps(fn)
    async def wrapper(
        mensagem: MensagemSerializador,
        uow: UnidadeDeTrabalho,
    ) -> ResultadoMensagem:
        for tentativa in range(2):
            try:
                return await fn(mensagem, uow)
            except IntegrityError:
                await uow.rollback()

                if await uow.leitura.mensagem_existe(mensagem.message_id):
                    return ResultadoMensagem.DUPLICADA

                if tentativa == 1:
                    raise

    return wrapper


@idempotente_em_conflito
async def receber_mensagem(
    mensagem: MensagemSerializador, uow: UnidadeDeTrabalho
) -> ResultadoMensagem:
    repo_dominio: ConversaDominioRepositorio = uow.dominio
    repo_leitura: ConversaLeituraRepositorio = uow.leitura

    if await repo_leitura.mensagem_existe(mensagem.message_id):
        return ResultadoMensagem.DUPLICADA

    # Busca se existe conversa
    conversa = await repo_leitura.buscar_por_empresa_e_telefone(
        mensagem.tenant_id, mensagem.telefone
    )
    if conversa is None:
        # Inicia-se uma conversa
        conversa = Conversa(
            tenant_id=mensagem.tenant_id,
            lead_id=None,
            telefone=mensagem.telefone,
        )

    # Adiciona uma mensagem a conversa
    conversa.receber_mensagem(
        Mensagem(
            id=None,
            identificador_da_mensagem=mensagem.message_id,
            conversa_id=None,
            texto=mensagem.texto,
            foi_enviada_pela_ia=False,
            foi_enviada_pelo_humano=False,
            criado_em=datetime.now(),
        )
    )

    await repo_dominio.salvar(conversa)
    return ResultadoMensagem.PROCESSADA
