from fastapi import APIRouter

from . import conversa, empresa, metricas

api_router = APIRouter()
api_router.include_router(conversa.router)
api_router.include_router(empresa.router)
api_router.include_router(metricas.router)
