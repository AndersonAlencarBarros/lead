import asyncio

from dominio.regras_de_negocio.servico_ia import construir_servico_ia
from exceptions import FalhaAoConsultarIA
from infraestrutura.celery_app import celery_app
from infraestrutura.session import Session
from servicos.executores.conversa import responder_conversa

TENTATIVAS_MAXIMAS = 3
ESPERA_BASE_ENTRE_TENTATIVAS_SEGUNDOS = 15
ESPERA_MAXIMA_ENTRE_TENTATIVAS_SEGUNDOS = 60


def criar_resposta_da_ia(
    tenant_id: str,
    telefone: str,
    mensagem_id: str,
    atraso: float = 0,
) -> None:
    responder_conversa_task.apply_async(
        args=(tenant_id, telefone, mensagem_id),
        countdown=atraso,
    )


async def _responder(
    tenant_id: str,
    telefone: str,
    mensagem_id: str,
) -> bool:
    try:
        return await responder_conversa(
            tenant_id,
            telefone,
            mensagem_id,
            construir_servico_ia(),
        )
    finally:
        await Session.dispose()


def _calcular_espera_entre_tentativas(tentativas_anteriores: int) -> int:
    """Backoff exponencial: 15s, 30s, 60s; limitado a 60s."""
    return min(
        ESPERA_MAXIMA_ENTRE_TENTATIVAS_SEGUNDOS,
        ESPERA_BASE_ENTRE_TENTATIVAS_SEGUNDOS * (2**tentativas_anteriores),
    )


@celery_app.task(
    bind=True,
    max_retries=TENTATIVAS_MAXIMAS,
    default_retry_delay=ESPERA_BASE_ENTRE_TENTATIVAS_SEGUNDOS,
)
def responder_conversa_task(
    self,
    tenant_id: str,
    telefone: str,
    mensagem_id: str,
) -> bool:
    try:
        return asyncio.run(_responder(tenant_id, telefone, mensagem_id))
    except FalhaAoConsultarIA as exc:
        espera_em_segundos = _calcular_espera_entre_tentativas(self.request.retries)
        raise self.retry(exc=exc, countdown=espera_em_segundos) from exc
