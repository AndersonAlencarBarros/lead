from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship

from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem
from infraestrutura.base import Base, mapper_registry

conversas_tabela = Table(
    "conversas",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column("tenant_id", String(255), nullable=False),
    Column(
        "lead_id",
        Uuid(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    ),
    Column("telefone", String(11), nullable=False),
    Column("teve_intervencao_humana", Boolean, nullable=False, default=False),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
    UniqueConstraint("tenant_id", "telefone"),
)

mensagens_tabela = Table(
    "mensagens",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column(
        "conversa_id",
        Uuid(as_uuid=True),
        ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "identificador_da_mensagem",
        String(255),
        unique=True,
        index=True,
        nullable=False,
    ),
    Column("texto", Text, nullable=False),
    Column("foi_gerada_pela_ia", Boolean, nullable=False, default=False),
    Column("foi_respondida_pelo_usuario", Boolean, nullable=False, default=False),
    Column("foi_intervencao_humana", Boolean, nullable=False, default=False),
    Column("simulacao", Boolean, nullable=False, default=False),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
)

# Mapeamento clássico (imperativo) direto para os objetos de domínio.
mapper_registry.map_imperatively(Mensagem, mensagens_tabela)

mapper_registry.map_imperatively(
    Conversa,
    conversas_tabela,
    properties={
        "mensagens": relationship(
            Mensagem,
            order_by=mensagens_tabela.c.criado_em,
            cascade="all, delete-orphan",
        ),
    },
)
