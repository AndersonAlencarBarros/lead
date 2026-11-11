from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import wraps
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.exc import IntegrityError

from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem, ResultadoMensagem
from infraestrutura import UnidadeDeTrabalho
from repositorio.conversa import ConversaDominioRepositorio
from servicos.serializadores.conversacao import MensagemSerializador

MENSAGEM_FORA_DO_HORARIO = (
    "Olá! Nosso atendimento automático funciona {horario}. "
    "No momento estamos fora desse horário. Deixe sua mensagem que "
    "responderemos quando o atendimento abrir."
)


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


def contexto_para_resposta_da_ia(
    conversa: Conversa,
) -> list[Mensagem] | None:
    """Tudo que o lead falou desde a última resposta da IA."""
    if not conversa.ia_pode_responder():
        return None

    return conversa.mensagens_pendentes() or None


def ultima_resposta_da_ia(conversa: Conversa) -> Mensagem | None:
    """Última mensagem gerada pela IA na conversa."""
    return max(
        (mensagem for mensagem in conversa.mensagens if mensagem.foi_gerada_pela_ia),
        key=lambda mensagem: mensagem.criado_em,
        default=None,
    )


def ultima_mensagem_de_intervencao_humana(
    conversa: Conversa,
) -> Mensagem | None:
    """Última mensagem enviada por humano da empresa na conversa."""
    return max(
        (
            mensagem
            for mensagem in conversa.mensagens
            if mensagem.foi_intervencao_humana
        ),
        key=lambda mensagem: mensagem.criado_em,
        default=None,
    )


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
            foi_gerada_pela_ia=True,
            foi_respondida_pelo_usuario=False,
            foi_intervencao_humana=False,
            criado_em=datetime.now(),
        )
    )

    try:
        await repo_dominio.salvar(conversa)
    except IntegrityError:
        await uow.rollback()
        return False

    return True


def _ultima_mensagem_do_usuario_sem_resposta(
    conversa: Conversa,
) -> Mensagem | None:
    """Última mensagem do lead posterior à última resposta da IA."""
    ultima_ia = ultima_resposta_da_ia(conversa)
    limite = ultima_ia.criado_em if ultima_ia is not None else None

    candidatas = [
        mensagem
        for mensagem in conversa.mensagens
        if mensagem.foi_respondida_pelo_usuario
        and (limite is None or mensagem.criado_em > limite)
    ]
    return max(candidatas, key=lambda mensagem: mensagem.criado_em, default=None)
