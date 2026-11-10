from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Uuid

from dominio.agregados.agendamento import Agendamento
from dominio.objetos_de_valor.agendamento import StatusDoAgendamento
from infraestrutura.base import Base, mapper_registry
from infraestrutura.orm.tipos import EnumString

agendamentos_tabela = Table(
    "agendamentos",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "empresa_id",
        Uuid(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "lead_id",
        Uuid(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("telefone", String(20), nullable=False),
    Column("horario_agendado", DateTime, nullable=False, index=True),
    Column("status", EnumString(StatusDoAgendamento), nullable=False),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
)

mapper_registry.map_imperatively(Agendamento, agendamentos_tabela)
