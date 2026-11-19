"""Consultas por cidade: busca, cidade mais próxima, UV atual, hoje e previsão."""

import math
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.current import CurrentState, resolve_current
from app.domain.daily import PeakWindow, best_windows, hours_at_or_above, peak_window
from app.models import City, UvForecastDaily, UvReading
from app.services.forecast import latest_daily, latest_hourly
from app.timeutil import local_now

DAY_START_HOUR = 6
DAY_END_HOUR = 19
EVENING_HOUR = 18


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def search_cities(session: Session, q: str | None) -> list[City]:
    cities = list(session.scalars(select(City).order_by(City.name)))
    if not q:
        return cities
    needle = _normalize(q.strip())
    return [c for c in cities if needle in _normalize(c.name)]


def nearest_city(session: Session, lat: float, lng: float) -> City | None:
    def distance_km(city: City) -> float:
        p1, p2 = math.radians(lat), math.radians(float(city.lat))
        dp = p2 - p1
        dl = math.radians(float(city.lng) - lng)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 6371 * 2 * math.asin(math.sqrt(a))

    return min(session.scalars(select(City)), key=distance_km, default=None)


def last_reading(session: Session, city_id: int) -> tuple[datetime, float] | None:
    """Última leitura; a real tem prioridade sobre a sintética no mesmo instante."""
    row = session.execute(
        select(UvReading.measured_at, UvReading.uv_index)
        .where(UvReading.city_id == city_id)
        .order_by(UvReading.measured_at.desc(), UvReading.origin.asc())
        .limit(1)
    ).first()
    return (row[0], float(row[1])) if row else None


def estimated_now(session: Session, city_id: int, now_utc: datetime) -> float | None:
    """Previsão para o instante atual, interpolada entre as duas horas mais próximas."""
    floor = now_utc.replace(minute=0, second=0, microsecond=0)
    points = dict(latest_hourly(session, city_id, floor, floor + timedelta(hours=2)))
    current = points.get(floor)
    if current is None:
        return None
    following = points.get(floor + timedelta(hours=1))
    if following is None:
        return current
    fraction = (now_utc - floor) / timedelta(hours=1)
    return round(current + (following - current) * fraction, 2)


def day_points(session: Session, city: City, d: date) -> list[tuple[datetime, float]]:
    """Previsão horária do dia local `d`, só entre 6h e 19h."""
    zone = ZoneInfo(city.timezone)
    start = datetime.combine(d, time(DAY_START_HOUR), tzinfo=zone)
    end = datetime.combine(d, time(DAY_END_HOUR), tzinfo=zone) + timedelta(hours=1)
    return latest_hourly(session, city.id, start, end)


@dataclass(frozen=True)
class NextPeak:
    date: date
    uv_max: float
    start: datetime | None
    end: datetime | None


def next_peak(session: Session, city: City, d: date) -> NextPeak | None:
    window: PeakWindow | None = peak_window(day_points(session, city, d))
    if window:
        return NextPeak(d, window.uv_max, window.start, window.end)
    daily: list[UvForecastDaily] = latest_daily(session, city.id, d, d + timedelta(days=1))
    return NextPeak(d, float(daily[0].uv_max), None, None) if daily else None


def current_for_city(
    session: Session, city: City, now_utc: datetime, settings: Settings
) -> tuple[CurrentState, NextPeak | None]:
    state = resolve_current(
        now_utc,
        city.timezone,
        last_reading(session, city.id),
        estimated_now(session, city.id, now_utc),
        settings.openuv_interval_min,
        (settings.collect_window_start_hour, settings.collect_window_end_hour),
    )
    peak = None
    if state.status == "night":
        local = local_now(now_utc, city.timezone)
        day = local.date() + timedelta(days=1) if local.hour >= EVENING_HOUR else local.date()
        peak = next_peak(session, city, day)
    return state, peak


@dataclass(frozen=True)
class TodayView:
    date: date
    points: list[tuple[datetime, float]]
    peak: PeakWindow | None
    best: list[tuple[datetime, datetime]]
    hours_above_8: int


def today_for_city(session: Session, city: City, now_utc: datetime) -> TodayView:
    today = local_now(now_utc, city.timezone).date()
    points = day_points(session, city, today)
    return TodayView(
        date=today,
        points=points,
        peak=peak_window(points),
        best=best_windows(points),
        hours_above_8=hours_at_or_above(points),
    )


def forecast_for_city(
    session: Session, city: City, now_utc: datetime, days: int = 5
) -> list[UvForecastDaily]:
    today = local_now(now_utc, city.timezone).date()
    return latest_daily(session, city.id, today, today + timedelta(days=days))
