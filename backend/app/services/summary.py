"""Resumo diário de UV por dia local da cidade.

O dado real sempre vence: um dia com leitura real vira `origin='real'` e nunca é
sobrescrito por dado sintético.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import City, UvDailySummary, UvReading
from app.services.forecast import latest_hourly
from app.timeutil import local_day_bounds_utc

HIGH_UV = 8.0


def refresh_summary(session: Session, city: City, d: date) -> None:
    start, end = local_day_bounds_utc(d, city.timezone)
    in_day = (
        UvReading.city_id == city.id,
        UvReading.measured_at >= start,
        UvReading.measured_at < end,
    )
    for origin in ("real", "sintetico"):
        uv_max, count_high, total = session.execute(
            select(
                func.max(func.greatest(UvReading.uv_index, func.coalesce(UvReading.uv_max, 0))),
                func.count().filter(UvReading.uv_index >= HIGH_UV),
                func.count(),
            ).where(*in_day, UvReading.origin == origin)
        ).one()
        if total:
            break
    else:
        return

    hours_above_8 = count_high
    if origin == "real":
        forecast = latest_hourly(session, city.id, start, end)
        if forecast:
            hours_above_8 = sum(1 for _, uv in forecast if uv >= HIGH_UV)

    stmt = insert(UvDailySummary).values(
        city_id=city.id, date=d, uv_max=uv_max, hours_above_8=hours_above_8, origin=origin
    )
    update = stmt.on_conflict_do_update(
        index_elements=[UvDailySummary.city_id, UvDailySummary.date],
        set_={
            "uv_max": stmt.excluded.uv_max,
            "hours_above_8": stmt.excluded.hours_above_8,
            "origin": stmt.excluded.origin,
        },
        # Sintético nunca sobrescreve um dia real.
        where=(UvDailySummary.origin == "sintetico") | (stmt.excluded.origin == "real"),
    )
    session.execute(update)
    session.flush()
