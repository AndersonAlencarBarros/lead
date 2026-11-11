from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from functools import wraps
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.exc import IntegrityError

from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem, ResultadoMensagem
from infraestrutura import UnidadeDeTrabalho
from repositorio.conversa import ConversaDominioRepositorio
from servicos.serializadores.conversacao import MensagemSerializador


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


def _mensagens_na_janela_de_resposta(
    conversa: Conversa,
    janela_de_resposta_em_segundos: float,
    agora: datetime,
) -> list[Mensagem]:
    """Mensagens dentro da janela de resposta da empresa."""
    limite = agora - timedelta(seconds=janela_de_resposta_em_segundos)
    return [mensagem for mensagem in conversa.mensagens if mensagem.criado_em >= limite]


def _pode_responder(conversa: Conversa) -> bool:
    return conversa.ia_pode_responder()


def _identificador_resposta(conversa: Conversa, mensagem_id: str) -> str:
    chave = f"{conversa.tenant_id}:{conversa.telefone}:{mensagem_id}"
    return f"ia:{uuid5(NAMESPACE_URL, chave)}"


async def _salvar_resposta_ia(
    conversa: Conversa,
    mensagem_id: str,
    texto: str,
    uow: UnidadeDeTrabalho,
) -> bool:
    repo_dominio: ConversaDominioRepositorio = uow.dominio

    conversa.receber_mensagem(
        Mensagem(
            identificador_da_mensagem=_identificador_resposta(conversa, mensagem_id),
            texto=texto,
            foi_enviada_pela_ia=True,
            foi_enviada_pelo_humano=False,
            criado_em=datetime.now(),
        )
    )

    try:
        await repo_dominio.salvar(conversa)
    except IntegrityError:
        await uow.rollback()
        return False

    return True
