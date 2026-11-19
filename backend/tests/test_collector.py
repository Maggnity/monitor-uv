import logging
from datetime import UTC, datetime, timedelta

from app.collector.jobs import collect_current, collect_forecast
from app.config import Settings
from app.models import UvForecastHourly, UvReading
from app.providers.base import (
    CurrentReading,
    DailyPoint,
    Forecast,
    HourlyPoint,
    ProviderError,
)
from app.seed.cities import seed_cities

SETTINGS = Settings(database_url="x")
# 14h em São Paulo / Fortaleza
AFTERNOON = datetime(2026, 11, 18, 17, 0, tzinfo=UTC)


class FakeCurrent:
    source = "openuv"

    def __init__(self, fail_for: set[str] | None = None):
        self.fail_for = fail_for or set()

    def fetch_current(self, city, now_utc=None):
        if city.station_code in self.fail_for:
            raise ProviderError("cota estourada", status=429)
        return CurrentReading(
            measured_at=datetime(2026, 11, 18, 16, 50, tzinfo=UTC),
            uv=7.5,
            uv_max=10.0,
            uv_max_at=datetime(2026, 11, 18, 15, 10, tzinfo=UTC),
            source=self.source,
        )


class FakeForecast:
    source = "openmeteo"

    def __init__(self, uv: float):
        self.uv = uv

    def fetch_forecast(self, city, now_utc=None):
        return Forecast(
            hourly=[HourlyPoint(datetime(2026, 11, 18, 15, 0, tzinfo=UTC), self.uv)],
            daily=[DailyPoint(AFTERNOON.date(), self.uv, 1)],
            source=self.source,
        )


def test_collect_current_skips_cities_outside_window(session):
    seed_cities(session)
    five_am_local = AFTERNOON.replace(hour=8)  # 05:00 em SP e Fortaleza
    assert collect_current(session, FakeCurrent(), five_am_local, SETTINGS) == 0
    assert session.query(UvReading).count() == 0


def test_collect_current_is_idempotent_for_same_timestamp(session):
    seed_cities(session)
    collect_current(session, FakeCurrent(), AFTERNOON, SETTINGS)
    collect_current(session, FakeCurrent(), AFTERNOON + timedelta(minutes=5), SETTINGS)
    assert session.query(UvReading).count() == 5
    assert {r.origin for r in session.query(UvReading)} == {"real"}


def test_collect_current_survives_provider_error(session, caplog):
    seed_cities(session)
    with caplog.at_level(logging.WARNING):
        saved = collect_current(session, FakeCurrent(fail_for={"SP-01"}), AFTERNOON, SETTINGS)
    assert saved == 4
    assert "SP-01" in caplog.text
    assert "429" in caplog.text


def test_collect_forecast_upserts_latest_value(session):
    seed_cities(session)
    collect_forecast(session, FakeForecast(5.0), AFTERNOON)
    collect_forecast(session, FakeForecast(8.0), AFTERNOON + timedelta(hours=1))
    rows = session.query(UvForecastHourly).filter_by(city_id=1).all()
    assert len(rows) == 1
    assert float(rows[0].uv_index) == 8.0
