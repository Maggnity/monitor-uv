from datetime import UTC, datetime, timedelta

from app.domain.current import resolve_current

TZ = "America/Sao_Paulo"
TWO_PM = datetime(2026, 11, 18, 17, 0, tzinfo=UTC)  # 14h em SP
ELEVEN_PM = datetime(2026, 11, 19, 2, 0, tzinfo=UTC)  # 23h em SP


def resolve(now, reading=None, estimated=None):
    return resolve_current(now, TZ, reading, estimated, interval_min=120, window=(6, 19))


def test_current_prefers_fresh_measurement():
    state = resolve(TWO_PM, (TWO_PM - timedelta(minutes=10), 9.0), 9.4)
    assert state.status == "ok"
    assert state.display_kind == "measured"
    assert state.display_uv == 9.0
    assert state.level.key == "very_high"


def test_current_uses_estimate_when_measurement_old():
    state = resolve(TWO_PM, (TWO_PM - timedelta(minutes=90), 7.0), 9.1)
    assert state.status == "ok"
    assert state.display_uv == 9.1
    assert state.display_kind == "estimated"
    assert state.measured_uv == 7.0


def test_current_night_has_precedence_over_stale():
    state = resolve(ELEVEN_PM, (ELEVEN_PM - timedelta(hours=7), 1.0), 0.0)
    assert state.status == "night"


def test_current_stale_inside_window_shows_last_measurement():
    reading = (TWO_PM - timedelta(hours=5), 6.0)
    assert resolve(TWO_PM, reading).status == "stale"
    with_estimate = resolve(TWO_PM, reading, 9.0)
    assert with_estimate.status == "stale"
    assert with_estimate.display_uv == 6.0
    assert with_estimate.display_kind == "measured"


def test_current_no_data():
    state = resolve(TWO_PM)
    assert state.status == "no_data"
    assert state.level is None
    assert state.display_uv is None


def test_current_not_stale_before_first_collection_of_the_day():
    six_thirty = datetime(2026, 11, 18, 9, 30, tzinfo=UTC)  # 06:30 em SP
    last_night = (six_thirty - timedelta(hours=11), 0.0)
    state = resolve(six_thirty, last_night, 0.8)
    assert state.status == "ok"
    assert state.display_kind == "estimated"
