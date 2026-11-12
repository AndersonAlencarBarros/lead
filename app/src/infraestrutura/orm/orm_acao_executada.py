from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)

from dominio.agregados.acao_executada import AcaoExecutada
from infraestrutura.base import Base, mapper_registry

acoes_executadas_tabela = Table(
    "acoes_executadas",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "turno_id",
        Uuid(as_uuid=True),
        ForeignKey("turnos_ia.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "conversa_id",
        Uuid(as_uuid=True),
        ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "lead_id",
        Uuid(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    ),
    Column("ferramenta", String(50), nullable=False),
    Column("argumentos", JSON, nullable=False),
    Column("resultado", JSON, nullable=True),
    Column("sucesso", Boolean, nullable=False, default=True),
    Column("erro", String(500), nullable=True),
    Column("hash_argumentos", String(64), nullable=False),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
    UniqueConstraint("turno_id", "ferramenta", "hash_argumentos"),
)

mapper_registry.map_imperatively(AcaoExecutada, acoes_executadas_tabela)
