"""Histórico por cidade e comparação entre cidades (painel de gestores)."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import City, UvDailySummary, UvReading
from app.services.cities import (
    DAY_END_HOUR,
    DAY_START_HOUR,
    current_for_city,
    day_points,
    forecast_for_city,
)
from app.services.forecast import latest_daily
from app.timeutil import local_day_bounds_utc, local_now

PERIOD_DAYS = {"7d": 7, "30d": 30, "12m": 365}
TREND_DAYS = 7
TREND_DELTA = 0.5

Trend = Literal["up", "down", "stable"]


@dataclass(frozen=True)
class HistoryDay:
    date: date
    uv_max: float
    origin: str  # real | sintetico | forecast


def summaries(session: Session, city_id: int, start: date, end: date) -> list[UvDailySummary]:
    """Resumos com data em [start, end)."""
    return list(
        session.scalars(
            select(UvDailySummary)
            .where(
                UvDailySummary.city_id == city_id,
                UvDailySummary.date >= start,
                UvDailySummary.date < end,
            )
            .order_by(UvDailySummary.date)
        )
    )


def today_peak(session: Session, city: City, today: date) -> float | None:
    points = day_points(session, city, today)
    if points:
        return max(uv for _, uv in points)
    daily = latest_daily(session, city.id, today, today + timedelta(days=1))
    return float(daily[0].uv_max) if daily else None


def history(session: Session, city: City, now_utc: datetime, period: str) -> list[HistoryDay]:
    today = local_now(now_utc, city.timezone).date()
    past = summaries(session, city.id, today - timedelta(days=PERIOD_DAYS[period]), today)
    days = [HistoryDay(s.date, float(s.uv_max), s.origin) for s in past]
    peak = today_peak(session, city, today)
    if peak is not None:
        days.append(HistoryDay(today, peak, "forecast"))
    return days


@dataclass(frozen=True)
class CompareRow:
    city: City
    current_uv: float | None
    current_kind: str | None
    peak_today: float | None
    hours_above_8: int
    trend: Trend
    sparkline: list[float]
    has_synthetic: bool


def _trend(peak: float | None, previous: list[float]) -> Trend:
    if peak is None or not previous:
        return "stable"
    delta = peak - sum(previous) / len(previous)
    if delta > TREND_DELTA:
        return "up"
    if delta < -TREND_DELTA:
        return "down"
    return "stable"


def compare_row(session: Session, city: City, now_utc: datetime, settings: Settings) -> CompareRow:
    today = local_now(now_utc, city.timezone).date()
    state, _ = current_for_city(session, city, now_utc, settings)
    points = day_points(session, city, today)
    peak = max((uv for _, uv in points), default=None)
    if peak is None:
        peak = today_peak(session, city, today)
    previous = summaries(session, city.id, today - timedelta(days=TREND_DAYS), today)
    previous_values = [float(s.uv_max) for s in previous]
    return CompareRow(
        city=city,
        current_uv=state.display_uv,
        current_kind=state.display_kind,
        peak_today=peak,
        hours_above_8=sum(1 for _, uv in points if uv >= 8),
        trend=_trend(peak, previous_values),
        sparkline=previous_values + ([peak] if peak is not None else []),
        has_synthetic=any(s.origin == "sintetico" for s in previous),
    )


def day_series(
    session: Session, city: City, d: date, now_utc: datetime
) -> tuple[list[tuple[datetime, float]], bool]:
    """Curva horária (6h–19h) do dia `d`. Hoje: previsão. Passado: leituras (real vence
    sintético), completadas pela previsão nas horas sem leitura. Retorna (pontos, tem_sintético)."""
    forecast = dict(day_points(session, city, d))
    today = local_now(now_utc, city.timezone).date()
    if d >= today:
        return sorted(forecast.items()), False

    start, end = local_day_bounds_utc(d, city.timezone)
    zone = ZoneInfo(city.timezone)
    by_hour: dict[datetime, tuple[str, float]] = {}
    readings = session.execute(
        select(UvReading.measured_at, UvReading.uv_index, UvReading.origin).where(
            UvReading.city_id == city.id,
            UvReading.measured_at >= start,
            UvReading.measured_at < end,
        )
    )
    for measured_at, uv, origin in readings:
        local = measured_at.astimezone(zone)
        if not DAY_START_HOUR <= local.hour <= DAY_END_HOUR:
            continue
        hour = local.replace(minute=0, second=0, microsecond=0).astimezone(measured_at.tzinfo)
        if hour not in by_hour or (origin == "real" and by_hour[hour][0] != "real"):
            by_hour[hour] = (origin, float(uv))
    merged = dict(forecast)
    merged.update({h: uv for h, (_, uv) in by_hour.items()})
    has_synthetic = any(origin == "sintetico" for origin, _ in by_hour.values())
    return sorted(merged.items()), has_synthetic


@dataclass(frozen=True)
class MapPoint:
    city: City
    uv: float | None
    kind: str | None


def map_points(
    session: Session, cities: list[City], now_utc: datetime, settings: Settings, when: str
) -> list[MapPoint]:
    result: list[MapPoint] = []
    for city in cities:
        today = local_now(now_utc, city.timezone).date()
        if when == "now":
            state, _ = current_for_city(session, city, now_utc, settings)
            result.append(MapPoint(city, state.display_uv, state.display_kind))
        elif when == "peak_today":
            result.append(MapPoint(city, today_peak(session, city, today), "forecast"))
        else:
            tomorrow = [d for d in forecast_for_city(session, city, now_utc) if d.date > today]
            peak = (
                float(tomorrow[0].uv_max)
                if tomorrow
                else today_peak(session, city, today + timedelta(days=1))
            )
            result.append(MapPoint(city, peak, "forecast"))
    return result
