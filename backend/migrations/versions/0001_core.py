"""Tabelas principais: cidades, leituras, previsões, resumos diários e alertas.

Revision ID: 0001
Revises:
Create Date: 2026-11-18 22:08:40.503390
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "city",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("lat", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("lng", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("station_code", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("station_code"),
    )
    op.create_table(
        "alert",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=4, scale=1), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("threshold BETWEEN 1 AND 15", name="ck_alert_threshold_range"),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_client", "alert", ["client_id"], unique=False)
    op.create_table(
        "uv_daily_summary",
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("uv_max", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("hours_above_8", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(length=10), nullable=False),
        sa.CheckConstraint("origin IN ('real', 'sintetico')", name="ck_summary_origin"),
        sa.CheckConstraint("uv_max >= 0", name="ck_summary_uv_non_negative"),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("city_id", "date"),
    )
    op.create_table(
        "uv_forecast_daily",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("uv_max", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("weather_code", sa.Integer(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.CheckConstraint("uv_max >= 0", name="ck_forecast_daily_uv_non_negative"),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "date", "source", name="uq_forecast_daily"),
    )
    op.create_table(
        "uv_forecast_hourly",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("forecast_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uv_index", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.CheckConstraint("uv_index >= 0", name="ck_forecast_hourly_uv_non_negative"),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "forecast_for", "source", name="uq_forecast_hourly"),
    )
    op.create_table(
        "uv_reading",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uv_index", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("uv_max", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("uv_max_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("origin", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("origin IN ('real', 'sintetico')", name="ck_uv_reading_origin"),
        sa.CheckConstraint("uv_index >= 0", name="ck_uv_reading_uv_non_negative"),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "city_id", "measured_at", "source", name="uq_uv_reading_city_time_source"
        ),
    )
    op.create_index(
        "ix_uv_reading_city_measured_desc",
        "uv_reading",
        ["city_id", sa.text("measured_at DESC")],
        unique=False,
    )
    op.create_table(
        "alert_trigger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("reading_id", sa.Integer(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alert.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reading_id"], ["uv_reading.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_trigger_alert_id"), "alert_trigger", ["alert_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_trigger_alert_id"), table_name="alert_trigger")
    op.drop_table("alert_trigger")
    op.drop_index("ix_uv_reading_city_measured_desc", table_name="uv_reading")
    op.drop_table("uv_reading")
    op.drop_table("uv_forecast_hourly")
    op.drop_table("uv_forecast_daily")
    op.drop_table("uv_daily_summary")
    op.drop_index("ix_alert_client", table_name="alert")
    op.drop_table("alert")
    op.drop_table("city")
