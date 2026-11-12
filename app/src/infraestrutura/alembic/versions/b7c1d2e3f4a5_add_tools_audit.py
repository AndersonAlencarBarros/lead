"""add playbook support, lead memory, tool turns and audit

Revision ID: b7c1d2e3f4a5
Revises: a4b623bca946
Create Date: 2026-11-11 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c1d2e3f4a5"
down_revision: str | Sequence[str] | None = "a4b623bca946"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "mensagens",
        sa.Column(
            "simulacao",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_table(
        "turnos_ia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversa_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("mensagem_origem_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("modelo", sa.String(length=255), nullable=True),
        sa.Column("tokens_entrada", sa.Integer(), nullable=False),
        sa.Column("tokens_saida", sa.Integer(), nullable=False),
        sa.Column("custo_estimado", sa.Float(), nullable=False),
        sa.Column("latencia_ms", sa.Integer(), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversa_id"],
            ["conversas.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversa_id", "mensagem_origem_id"),
    )
    op.create_index(
        op.f("ix_turnos_ia_conversa_id"),
        "turnos_ia",
        ["conversa_id"],
    )
    op.create_index(
        op.f("ix_turnos_ia_tenant_id"),
        "turnos_ia",
        ["tenant_id"],
    )
    op.create_table(
        "auditorias",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("turno_id", sa.Uuid(), nullable=False),
        sa.Column("conversa_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("ferramenta", sa.String(length=50), nullable=False),
        sa.Column("argumentos", sa.JSON(), nullable=False),
        sa.Column("resultado", sa.JSON(), nullable=True),
        sa.Column("sucesso", sa.Boolean(), nullable=False),
        sa.Column("erro", sa.String(length=500), nullable=True),
        sa.Column("hash_argumentos", sa.String(length=64), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversa_id"],
            ["conversas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["turno_id"],
            ["turnos_ia.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("turno_id", "ferramenta", "hash_argumentos"),
    )
    op.create_index(
        op.f("ix_auditorias_conversa_id"),
        "auditorias",
        ["conversa_id"],
    )
    op.create_index(
        op.f("ix_auditorias_lead_id"),
        "auditorias",
        ["lead_id"],
    )
    op.create_index(
        op.f("ix_auditorias_turno_id"),
        "auditorias",
        ["turno_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_auditorias_turno_id"),
        table_name="auditorias",
    )
    op.drop_index(
        op.f("ix_auditorias_lead_id"),
        table_name="auditorias",
    )
    op.drop_index(
        op.f("ix_auditorias_conversa_id"),
        table_name="auditorias",
    )
    op.drop_table("auditorias")
    op.drop_index(op.f("ix_turnos_ia_tenant_id"), table_name="turnos_ia")
    op.drop_index(op.f("ix_turnos_ia_conversa_id"), table_name="turnos_ia")
    op.drop_table("turnos_ia")
    op.drop_column("mensagens", "simulacao")
