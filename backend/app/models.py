"""Modelos do banco: cidades, leituras, previsões, resumos diários e alertas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

UV = Numeric(4, 2)


class City(Base):
    __tablename__ = "city"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2))
    lat: Mapped[float] = mapped_column(Numeric(9, 6))
    lng: Mapped[float] = mapped_column(Numeric(9, 6))
    timezone: Mapped[str] = mapped_column(String(64))
    station_code: Mapped[str] = mapped_column(String(20), unique=True)


class UvReading(Base):
    """Leitura de UV medida (ou simulada) em um instante."""

    __tablename__ = "uv_reading"
    __table_args__ = (
        UniqueConstraint("city_id", "measured_at", "source", name="uq_uv_reading_city_time_source"),
        Index(
            "ix_uv_reading_city_measured_desc",
            "city_id",
            "measured_at",
            postgresql_ops={"measured_at": "DESC"},
        ),
        CheckConstraint("uv_index >= 0", name="ck_uv_reading_uv_non_negative"),
        CheckConstraint("origin IN ('real', 'sintetico')", name="ck_uv_reading_origin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id", ondelete="CASCADE"))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    uv_index: Mapped[Decimal] = mapped_column(UV)
    uv_max: Mapped[Decimal | None] = mapped_column(UV)
    uv_max_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped[City] = relationship()


class UvForecastHourly(Base):
    __tablename__ = "uv_forecast_hourly"
    __table_args__ = (
        UniqueConstraint("city_id", "forecast_for", "source", name="uq_forecast_hourly"),
        CheckConstraint("uv_index >= 0", name="ck_forecast_hourly_uv_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id", ondelete="CASCADE"))
    forecast_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    uv_index: Mapped[Decimal] = mapped_column(UV)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(20))


class UvForecastDaily(Base):
    __tablename__ = "uv_forecast_daily"
    __table_args__ = (
        UniqueConstraint("city_id", "date", "source", name="uq_forecast_daily"),
        CheckConstraint("uv_max >= 0", name="ck_forecast_daily_uv_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    uv_max: Mapped[Decimal] = mapped_column(UV)
    weather_code: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(20))


class UvDailySummary(Base):
    """Resumo por dia local da cidade; alimenta histórico e mapa de calor."""

    __tablename__ = "uv_daily_summary"
    __table_args__ = (
        CheckConstraint("origin IN ('real', 'sintetico')", name="ck_summary_origin"),
        CheckConstraint("uv_max >= 0", name="ck_summary_uv_non_negative"),
    )

    city_id: Mapped[int] = mapped_column(
        ForeignKey("city.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    uv_max: Mapped[Decimal] = mapped_column(UV)
    hours_above_8: Mapped[int] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(String(10))


class Alert(Base):
    __tablename__ = "alert"
    __table_args__ = (
        CheckConstraint("threshold BETWEEN 1 AND 15", name="ck_alert_threshold_range"),
        Index("ix_alert_client", "client_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id", ondelete="CASCADE"))
    threshold: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped[City] = relationship()


class AlertTrigger(Base):
    __tablename__ = "alert_trigger"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alert.id", ondelete="CASCADE"), index=True)
    reading_id: Mapped[int] = mapped_column(ForeignKey("uv_reading.id", ondelete="CASCADE"))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
