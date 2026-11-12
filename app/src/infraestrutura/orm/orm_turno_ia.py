from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)

from dominio.agregados.turno_ia import StatusTurno, TurnoIA
from infraestrutura.base import Base, mapper_registry
from infraestrutura.orm.tipos import EnumString

turnos_ia_tabela = Table(
    "turnos_ia",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "conversa_id",
        Uuid(as_uuid=True),
        ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("tenant_id", String(255), nullable=False, index=True),
    Column("mensagem_origem_id", String(255), nullable=False),
    Column("status", EnumString(StatusTurno), nullable=False),
    Column("modelo", String(255), nullable=True),
    Column("tokens_entrada", Integer, nullable=False, default=0),
    Column("tokens_saida", Integer, nullable=False, default=0),
    Column("custo_estimado", Float, nullable=False, default=0.0),
    Column("latencia_ms", Integer, nullable=False, default=0),
    Column("erro", Text, nullable=True),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
    UniqueConstraint("conversa_id", "mensagem_origem_id"),
)

mapper_registry.map_imperatively(TurnoIA, turnos_ia_tabela)
