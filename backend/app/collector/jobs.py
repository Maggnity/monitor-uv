"""Rotinas de coleta: UV atual e previsão, gravadas com upsert."""

import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import City, UvForecastDaily, UvForecastHourly, UvReading
from app.providers.base import CurrentProvider, ForecastProvider, ProviderError
from app.services.alerts import evaluate_alerts
from app.services.summary import refresh_summary
from app.timeutil import local_date, local_now

logger = logging.getLogger(__name__)


def in_collect_window(now_utc: datetime, city: City, settings: Settings) -> bool:
    hour = local_now(now_utc, city.timezone).hour
    return settings.collect_window_start_hour <= hour <= settings.collect_window_end_hour


def _origin(source: str) -> str:
    return "sintetico" if source == "simulado" else "real"


def collect_current(
    session: Session, provider: CurrentProvider, now_utc: datetime, settings: Settings
) -> int:
    """Grava a leitura atual de cada cidade dentro da janela de coleta. Retorna quantas gravou."""
    saved = 0
    for city in session.query(City).order_by(City.id):
        if not in_collect_window(now_utc, city, settings):
            continue
        try:
            current = provider.fetch_current(city, now_utc)
        except ProviderError as exc:
            logger.warning(
                "Falha ao coletar UV de %s (%s): status=%s %s",
                city.name,
                city.station_code,
                exc.status,
                exc,
            )
            continue
        values = {
            "city_id": city.id,
            "measured_at": current.measured_at,
            "uv_index": current.uv,
            "uv_max": current.uv_max,
            "uv_max_at": current.uv_max_at,
            "source": current.source,
            "origin": _origin(current.source),
        }
        stmt = insert(UvReading).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_uv_reading_city_time_source",
            set_={k: stmt.excluded[k] for k in ("uv_index", "uv_max", "uv_max_at")},
        ).returning(UvReading)
        reading = session.scalars(stmt).one()
        session.flush()
        refresh_summary(session, city, local_date(current.measured_at, city.timezone))
        evaluate_alerts(session, reading, city)
        session.commit()
        saved += 1
        logger.info("UV %s: %.2f (%s)", city.station_code, current.uv, current.source)
    return saved


def collect_forecast(session: Session, provider: ForecastProvider, now_utc: datetime) -> int:
    """Grava a previsão horária e diária de cada cidade. Retorna quantas cidades atualizou."""
    updated = 0
    for city in session.query(City).order_by(City.id):
        try:
            forecast = provider.fetch_forecast(city, now_utc)
        except ProviderError as exc:
            logger.warning(
                "Falha ao coletar previsão de %s: status=%s %s", city.station_code, exc.status, exc
            )
            continue
        if forecast.hourly:
            stmt = insert(UvForecastHourly).values(
                [
                    {
                        "city_id": city.id,
                        "forecast_for": p.forecast_for,
                        "uv_index": p.uv,
                        "fetched_at": now_utc,
                        "source": forecast.source,
                    }
                    for p in forecast.hourly
                ]
            )
            session.execute(
                stmt.on_conflict_do_update(
                    constraint="uq_forecast_hourly",
                    set_={
                        "uv_index": stmt.excluded.uv_index,
                        "fetched_at": stmt.excluded.fetched_at,
                    },
                )
            )
        if forecast.daily:
            stmt = insert(UvForecastDaily).values(
                [
                    {
                        "city_id": city.id,
                        "date": p.date,
                        "uv_max": p.uv_max,
                        "weather_code": p.weather_code,
                        "fetched_at": now_utc,
                        "source": forecast.source,
                    }
                    for p in forecast.daily
                ]
            )
            session.execute(
                stmt.on_conflict_do_update(
                    constraint="uq_forecast_daily",
                    set_={
                        "uv_max": stmt.excluded.uv_max,
                        "weather_code": stmt.excluded.weather_code,
                        "fetched_at": stmt.excluded.fetched_at,
                    },
                )
            )
        session.commit()
        updated += 1
    return updated
