from fastapi import APIRouter, status

from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.empresa import criar_empresa
from servicos.serializadores.empresa import (
    EmpresaCriacaoSerializador,
    EmpresaResposta,
)

router = APIRouter()


@router.post(
    "/empresas",
    response_model=EmpresaResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["Empresas"],
    summary="Criar empresa",
    description="Cadastra uma empresa para um tenant.",
    responses={409: {"description": "Tenant já cadastrado"}},
)
async def criar_empresa_api(payload: EmpresaCriacaoSerializador):
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        return await criar_empresa(payload, uow)
