"""Histórico sintético de demonstração (nenhuma API gratuita fornece 12 meses de UV).

Gera dados só até ontem, nunca toca dias que já têm resumo (real ou sintético) e é
idempotente: rodar de novo só preenche os dias que faltam.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.synthetic import PEAK_BASE, PEAK_HOUR, bell_uv, day_rng, seasonal_peak
from app.models import City, UvDailySummary, UvReading

HOURS = range(6, 20)


def seed_history(
    session: Session, today_local: date, days_hourly: int = 30, days_daily: int = 365
) -> int:
    created = 0
    for city in session.query(City).order_by(City.id):
        existing = set(
            session.scalars(
                select(UvDailySummary.date).where(
                    UvDailySummary.city_id == city.id,
                    UvDailySummary.date >= today_local - timedelta(days=days_daily),
                )
            )
        )
        zone = ZoneInfo(city.timezone)
        summaries: list[dict] = []
        readings: list[dict] = []
        for offset in range(days_daily, 0, -1):
            day = today_local - timedelta(days=offset)
            if day in existing:
                continue
            peak = seasonal_peak(
                PEAK_BASE.get(city.station_code, 10),
                float(city.lat),
                day,
                day_rng(city.station_code, day),
            )
            curve = {h: bell_uv(h, peak) for h in HOURS}
            summaries.append(
                {
                    "city_id": city.id,
                    "date": day,
                    "uv_max": bell_uv(PEAK_HOUR, peak),
                    "hours_above_8": sum(1 for uv in curve.values() if uv >= 8),
                    "origin": "sintetico",
                }
            )
            if offset <= days_hourly:
                readings.extend(
                    {
                        "city_id": city.id,
                        "measured_at": datetime(day.year, day.month, day.day, h, tzinfo=zone),
                        "uv_index": uv,
                        "source": "simulado",
                        "origin": "sintetico",
                    }
                    for h, uv in curve.items()
                )
        if summaries:
            session.execute(insert(UvDailySummary).values(summaries).on_conflict_do_nothing())
        if readings:
            session.execute(insert(UvReading).values(readings).on_conflict_do_nothing())
        created += len(summaries)
    session.commit()
    return created
