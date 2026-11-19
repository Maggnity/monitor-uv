import random
from datetime import date, timedelta

from app.domain.synthetic import bell_uv, seasonal_peak


def test_bell_uv_zero_at_night_and_peak_near_noon():
    assert bell_uv(3, 10) == 0
    assert bell_uv(12.25, 10) == 10
    assert bell_uv(20, 10) == 0


def test_seasonal_peak_fortaleza_stays_between_11_and_14():
    rng = random.Random(1)
    for offset in range(365):
        d = date(2026, 1, 1) + timedelta(days=offset)
        assert 11 <= seasonal_peak(13, -3.73, d, rng) <= 14.5


def test_seasonal_peak_curitiba_is_higher_in_summer_than_winter():
    rng = random.Random(1)
    assert seasonal_peak(9, -25.43, date(2026, 12, 21), rng) > seasonal_peak(
        9, -25.43, date(2026, 6, 21), rng
    )
