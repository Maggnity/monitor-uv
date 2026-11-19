from datetime import UTC, datetime

from app.domain.daily import best_windows, hours_at_or_above, peak_window


def h(hour: int) -> datetime:
    return datetime(2026, 11, 18, hour, 0, tzinfo=UTC)


def test_peak_window_formats_plateau():
    points = [(h(10), 8), (h(11), 10.5), (h(12), 11), (h(13), 10), (h(14), 7)]
    window = peak_window(points)
    assert window.start == h(11)
    assert window.end == h(14)
    assert window.uv_max == 11


def test_peak_window_none_when_dark():
    assert peak_window([(h(3), 0), (h(4), 0.2)]) is None


def test_best_windows_morning_and_evening():
    values = [0.5, 1.8, 3, 5, 7, 9, 10, 9, 7, 5, 3, 2.5, 1.2]
    points = [(h(6 + i), uv) for i, uv in enumerate(values)]
    assert best_windows(points) == [(h(6), h(8)), (h(18), h(19))]


def test_hours_at_or_above_counts_inclusive():
    assert hours_at_or_above([(h(11), 8), (h(12), 9), (h(13), 7.9)]) == 2
