"""create conversas and mensagens tables

Revision ID: 7f3a1c9b2d4e
Revises: 0001_baseline
Create Date: 2026-11-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f3a1c9b2d4e"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "conversas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("telefone", sa.String(length=11), nullable=False),
        sa.Column("teve_intervencao_humana", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_id"),
        sa.UniqueConstraint("tenant_id", "telefone"),
    )
    op.create_table(
        "mensagens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversa_id", sa.Uuid(), nullable=False),
        sa.Column("identificador_da_mensagem", sa.String(length=255), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("foi_gerada_pela_ia", sa.Boolean(), nullable=False),
        sa.Column("foi_respondida_pelo_usuario", sa.Boolean(), nullable=False),
        sa.Column("foi_intervencao_humana", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mensagens_conversa_id"), "mensagens", ["conversa_id"])
    op.create_index(
        op.f("ix_mensagens_identificador_da_mensagem"),
        "mensagens",
        ["identificador_da_mensagem"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_mensagens_identificador_da_mensagem"), table_name="mensagens"
    )
    op.drop_index(op.f("ix_mensagens_conversa_id"), table_name="mensagens")
    op.drop_table("mensagens")
    op.drop_table("conversas")
