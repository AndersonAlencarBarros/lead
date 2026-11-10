from fastapi import APIRouter

from . import conversa, empresa

api_router = APIRouter()
api_router.include_router(conversa.router)
api_router.include_router(empresa.router)
