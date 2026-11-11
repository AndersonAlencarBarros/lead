from celery import Celery

from config import get_settings

settings = get_settings()

celery_app = Celery(
    "motor_ia",
    broker=settings.celery_broker_url,
    include=["dominio.regras_de_negocio.servico_ia.responder_conversa"],
)

celery_app.conf.update(
    task_ignore_result=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
