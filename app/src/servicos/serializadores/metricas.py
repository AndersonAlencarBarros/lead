from pydantic import BaseModel, Field


class MetricasResposta(BaseModel):
    tenant_id: str = Field(description="Identificador do tenant.")
    total_conversas: int = Field(description="Total de conversas do tenant.")
    custo_medio_por_conversa: float = Field(
        description="Custo médio estimado por conversa."
    )
    percentual_qualificados: float = Field(
        description="Percentual de leads com tag qualificado."
    )
    percentual_transferidos: float = Field(
        description="Percentual de conversas transferidas para humano."
    )
