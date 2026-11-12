from fastapi import APIRouter, status

from servicos.serializadores.metricas import MetricasResposta
from servicos.visualizadores.metricas import obter_metricas

router = APIRouter()


@router.get(
    "/metricas/{tenant_id}",
    response_model=MetricasResposta,
    status_code=status.HTTP_200_OK,
    tags=["Métricas"],
    summary="Métricas do tenant",
    description=(
        "Retorna total de conversas, custo médio por conversa, percentual de "
        "qualificados e percentual de transferidos para humano."
    ),
)
async def metricas_api(tenant_id: str) -> MetricasResposta:
    return await obter_metricas(tenant_id)
