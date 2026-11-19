"""Consultas de previsão: sempre a versão mais recente de cada hora/dia, de qualquer fonte."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.models import UvForecastDaily, UvForecastHourly


def latest_hourly(
    session: Session, city_id: int, start: datetime, end: datetime
) -> list[tuple[datetime, float]]:
    """Previsão horária em [start, end), ordenada por hora."""
    stmt = (
        select(UvForecastHourly.forecast_for, UvForecastHourly.uv_index)
        .where(
            UvForecastHourly.city_id == city_id,
            UvForecastHourly.forecast_for >= start,
            UvForecastHourly.forecast_for < end,
        )
        .ext(distinct_on(UvForecastHourly.forecast_for))
        .order_by(UvForecastHourly.forecast_for, UvForecastHourly.fetched_at.desc())
    )
    return [(t, float(uv)) for t, uv in session.execute(stmt)]


def latest_daily(session: Session, city_id: int, start: date, end: date) -> list[UvForecastDaily]:
    """Previsão diária com data em [start, end), ordenada por data."""
    stmt = (
        select(UvForecastDaily)
        .where(
            UvForecastDaily.city_id == city_id,
            UvForecastDaily.date >= start,
            UvForecastDaily.date < end,
        )
        .ext(distinct_on(UvForecastDaily.date))
        .order_by(UvForecastDaily.date, UvForecastDaily.fetched_at.desc())
    )
    return list(session.scalars(stmt))
