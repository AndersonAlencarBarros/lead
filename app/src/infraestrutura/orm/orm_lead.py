from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)

from dominio.agregados.lead import Lead
from infraestrutura.base import Base, mapper_registry

leads_tabela = Table(
    "leads",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "empresa_id",
        Uuid(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("nome", String(255), nullable=True),
    Column("telefone", String(20), nullable=True),
    Column("cidade", String(255), nullable=True),
    Column("estagio", String(20), nullable=True),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
    UniqueConstraint("empresa_id", "telefone"),
)

mapper_registry.map_imperatively(Lead, leads_tabela)
