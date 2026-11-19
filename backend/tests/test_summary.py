from datetime import UTC, date, datetime

from app.models import UvDailySummary
from app.seed.cities import seed_cities
from app.services.summary import refresh_summary
from tests.factories import add_hourly, add_reading, city


def test_refresh_summary_real_wins_over_synthetic(session):
    seed_cities(session)
    sp = city(session)
    add_reading(session, sp.id, datetime(2026, 11, 10, 15, 0, tzinfo=UTC), 11, origin="sintetico")
    add_reading(session, sp.id, datetime(2026, 11, 10, 16, 0, tzinfo=UTC), 6.5, origin="real")
    refresh_summary(session, sp, date(2026, 11, 10))
    summary = session.get(UvDailySummary, (sp.id, date(2026, 11, 10)))
    assert summary.origin == "real"
    assert float(summary.uv_max) == 6.5


def test_refresh_summary_uses_local_day(session):
    seed_cities(session)
    sp = city(session)
    # 22:30 em São Paulo, ainda dia 18
    add_reading(session, sp.id, datetime(2026, 11, 19, 1, 30, tzinfo=UTC), 0.4, uv_max=10.2)
    refresh_summary(session, sp, date(2026, 11, 18))
    summary = session.get(UvDailySummary, (sp.id, date(2026, 11, 18)))
    assert float(summary.uv_max) == 10.2
    assert session.get(UvDailySummary, (sp.id, date(2026, 11, 19))) is None


def test_refresh_summary_counts_forecast_hours_above_8_for_real_days(session):
    seed_cities(session)
    sp = city(session)
    add_reading(session, sp.id, datetime(2026, 11, 18, 15, 0, tzinfo=UTC), 9)
    for hour, uv in [(14, 8.0), (15, 9.5), (16, 7.9)]:
        add_hourly(session, sp.id, datetime(2026, 11, 18, hour, 0, tzinfo=UTC), uv)
    refresh_summary(session, sp, date(2026, 11, 18))
    assert session.get(UvDailySummary, (sp.id, date(2026, 11, 18))).hours_above_8 == 2
