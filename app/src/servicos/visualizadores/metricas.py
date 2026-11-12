from sqlalchemy import func, select

import infraestrutura.orm  # noqa: F401
from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.agregados.lead import Lead
from dominio.agregados.turno_ia import TurnoIA
from infraestrutura.session import Session
from servicos.serializadores.metricas import MetricasResposta


async def obter_metricas(tenant_id: str) -> MetricasResposta:
    async with Session() as session:
        total_conversas = await session.scalar(
            select(func.count())
            .select_from(Conversa)
            .where(Conversa.tenant_id == tenant_id)
        )
        transferidas = await session.scalar(
            select(func.count())
            .select_from(Conversa)
            .where(
                (Conversa.tenant_id == tenant_id)
                & (Conversa.teve_intervencao_humana.is_(True))
            )
        )
        custo_total, conversas_com_turno = (
            await session.execute(
                select(
                    func.coalesce(func.sum(TurnoIA.custo_estimado), 0.0),
                    func.count(func.distinct(TurnoIA.conversa_id)),
                ).where(TurnoIA.tenant_id == tenant_id)
            )
        ).one()

        empresa = await session.scalar(
            select(Empresa).where(Empresa.tenant_id == tenant_id)
        )
        leads = []
        if empresa is not None:
            resultado = await session.execute(
                select(Lead).where(Lead.empresa_id == empresa.id)
            )
            leads = list(resultado.scalars().all())

    total = int(total_conversas or 0)
    transferidas_total = int(transferidas or 0)
    conversas_com_turno = int(conversas_com_turno or 0)
    leads_com_tag = [lead for lead in leads if lead.tags]
    qualificados = [lead for lead in leads_com_tag if "qualificado" in lead.tags]

    return MetricasResposta(
        tenant_id=tenant_id,
        total_conversas=total,
        custo_medio_por_conversa=(
            float(custo_total) / conversas_com_turno if conversas_com_turno else 0.0
        ),
        percentual_qualificados=(
            100.0 * len(qualificados) / len(leads_com_tag) if leads_com_tag else 0.0
        ),
        percentual_transferidos=(100.0 * transferidas_total / total if total else 0.0),
    )
