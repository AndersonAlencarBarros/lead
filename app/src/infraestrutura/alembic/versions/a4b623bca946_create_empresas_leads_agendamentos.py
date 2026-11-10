"""create empresas leads agendamentos

Revision ID: a4b623bca946
Revises: 7f3a1c9b2d4e
Create Date: 2026-11-10 12:03:52.275141

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4b623bca946"
down_revision: str | Sequence[str] | None = "7f3a1c9b2d4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "empresas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("telefone_notificacao", sa.String(length=20), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("janela_de_resposta", sa.Float(), nullable=False),
        sa.Column("configuracoes", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("cidade", sa.String(length=255), nullable=True),
        sa.Column("estagio", sa.String(length=20), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresas.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "telefone"),
    )
    op.create_index(op.f("ix_leads_empresa_id"), "leads", ["empresa_id"])
    op.create_table(
        "agendamentos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("telefone", sa.String(length=20), nullable=False),
        sa.Column("horario_agendado", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agendamentos_empresa_id"),
        "agendamentos",
        ["empresa_id"],
    )
    op.create_index(
        op.f("ix_agendamentos_lead_id"),
        "agendamentos",
        ["lead_id"],
    )
    op.create_index(
        op.f("ix_agendamentos_horario_agendado"),
        "agendamentos",
        ["horario_agendado"],
    )
    with op.batch_alter_table("conversas") as batch_op:
        batch_op.create_foreign_key(
            "fk_conversas_lead_id_leads",
            "leads",
            ["lead_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("conversas") as batch_op:
        batch_op.drop_constraint("fk_conversas_lead_id_leads", type_="foreignkey")
    op.drop_index(
        op.f("ix_agendamentos_horario_agendado"),
        table_name="agendamentos",
    )
    op.drop_index(op.f("ix_agendamentos_lead_id"), table_name="agendamentos")
    op.drop_index(op.f("ix_agendamentos_empresa_id"), table_name="agendamentos")
    op.drop_table("agendamentos")
    op.drop_index(op.f("ix_leads_empresa_id"), table_name="leads")
    op.drop_table("leads")
    op.drop_table("empresas")
