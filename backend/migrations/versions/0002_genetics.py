"""Camada genética: fototipos de pele e distribuição ilustrativa por cidade.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18 22:37:11.919894
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skin_phototype",
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("description", sa.String(length=120), nullable=False),
        sa.Column("med_j_m2", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.CheckConstraint("med_j_m2 > 0", name="ck_phototype_med_positive"),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "city_phototype_distribution",
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("phototype", sa.String(length=3), nullable=False),
        sa.Column("share", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column("is_illustrative", sa.Boolean(), nullable=False),
        sa.CheckConstraint("share >= 0 AND share <= 1", name="ck_distribution_share_range"),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["phototype"], ["skin_phototype.code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("city_id", "phototype"),
    )


def downgrade() -> None:
    op.drop_table("city_phototype_distribution")
    op.drop_table("skin_phototype")
