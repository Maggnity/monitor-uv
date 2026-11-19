from datetime import date

from app.models import UvDailySummary, UvReading
from app.seed.cities import seed_cities
from app.seed.history import seed_history

TODAY = date(2026, 11, 18)


def test_seed_history_stops_at_yesterday(session):
    seed_cities(session)
    seed_history(session, TODAY)
    dates = {s.date for s in session.query(UvDailySummary)}
    assert max(dates) == date(2026, 11, 17)
    assert date(2025, 11, 18) in dates
    assert all(r.origin == "sintetico" for r in session.query(UvReading))


def test_seed_history_is_idempotent(session):
    seed_cities(session)
    assert seed_history(session, TODAY) > 0
    assert seed_history(session, TODAY) == 0


def test_seed_history_does_not_overwrite_real_day(session):
    seed_cities(session)
    session.add(
        UvDailySummary(
            city_id=1, date=date(2026, 11, 10), uv_max=7.7, hours_above_8=0, origin="real"
        )
    )
    session.commit()
    seed_history(session, TODAY)
    summary = session.get(UvDailySummary, (1, date(2026, 11, 10)))
    assert float(summary.uv_max) == 7.7
    assert summary.origin == "real"
