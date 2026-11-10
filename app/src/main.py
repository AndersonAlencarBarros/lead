from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import api_router
from infraestrutura.session import Session


# Ciclo de vida da aplicação: o que vem antes do `yield` roda no startup e o
# que vem depois roda no shutdown. Aqui só o shutdown importa: fecha o pool de
# conexões do SQLAlchemy (`Session.dispose`) antes do processo morrer.
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await Session.dispose()


tags_metadata = [
    {"name": "Webhook", "description": "Recebimento de mensagens externas."},
    {"name": "Conversas", "description": "Consulta de conversas e mensagens."},
]

app = FastAPI(
    title="Motor IA",
    summary="API de atendimento por conversas",
    description=(
        "Gerencia conversas, mensagens e recebimento de webhooks de atendimento."
    ),
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(api_router)
