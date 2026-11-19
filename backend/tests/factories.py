"""Auxiliares de teste para inserir dados diretamente no banco."""

from datetime import UTC, datetime

from app.models import City, UvForecastDaily, UvForecastHourly, UvReading


def add_reading(session, city_id, measured_at, uv, *, origin="real", source=None, uv_max=None):
    reading = UvReading(
        city_id=city_id,
        measured_at=measured_at,
        uv_index=uv,
        uv_max=uv_max,
        source=source or ("openuv" if origin == "real" else "simulado"),
        origin=origin,
    )
    session.add(reading)
    session.flush()
    return reading


def add_hourly(session, city_id, forecast_for, uv, *, source="openmeteo", fetched_at=None):
    session.add(
        UvForecastHourly(
            city_id=city_id,
            forecast_for=forecast_for,
            uv_index=uv,
            fetched_at=fetched_at or datetime(2026, 11, 18, 0, 0, tzinfo=UTC),
            source=source,
        )
    )
    session.flush()


def add_daily(session, city_id, d, uv_max, *, weather_code=1, source="openmeteo"):
    session.add(
        UvForecastDaily(
            city_id=city_id,
            date=d,
            uv_max=uv_max,
            weather_code=weather_code,
            fetched_at=datetime(2026, 11, 18, 0, 0, tzinfo=UTC),
            source=source,
        )
    )
    session.flush()


def city(session, station_code="SP-01") -> City:
    return session.query(City).filter_by(station_code=station_code).one()
