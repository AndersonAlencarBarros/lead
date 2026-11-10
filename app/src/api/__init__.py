from fastapi import APIRouter

from . import conversa

api_router = APIRouter()
api_router.include_router(conversa.router)
