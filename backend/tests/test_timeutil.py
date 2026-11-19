from datetime import UTC, date, datetime

from app.timeutil import local_date, local_day_bounds_utc


def test_local_date_uses_city_timezone():
    assert local_date(datetime(2026, 11, 19, 2, 30, tzinfo=UTC), "America/Sao_Paulo") == date(
        2026, 11, 18
    )


def test_local_day_bounds_utc_for_sao_paulo():
    start, end = local_day_bounds_utc(date(2026, 11, 18), "America/Sao_Paulo")
    assert start == datetime(2026, 11, 18, 3, 0, tzinfo=UTC)
    assert end == datetime(2026, 11, 19, 3, 0, tzinfo=UTC)
