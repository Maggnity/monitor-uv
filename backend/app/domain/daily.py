"""Regras sobre a curva horária de um dia: pico, melhores horários e horas de UV alto."""

from dataclasses import dataclass
from datetime import datetime, timedelta

Points = list[tuple[datetime, float]]
HOUR = timedelta(hours=1)


@dataclass(frozen=True)
class PeakWindow:
    start: datetime
    end: datetime
    uv_max: float


def peak_window(points: Points) -> PeakWindow | None:
    """Janela contínua em torno do máximo com UV >= 90% do pico. `end` é exclusivo."""
    if not points:
        return None
    top = max(range(len(points)), key=lambda i: points[i][1])
    uv_max = points[top][1]
    if uv_max < 0.5:
        return None
    threshold = 0.9 * uv_max
    first = last = top
    while first > 0 and points[first - 1][1] >= threshold:
        first -= 1
    while last < len(points) - 1 and points[last + 1][1] >= threshold:
        last += 1
    return PeakWindow(points[first][0], points[last][0] + HOUR, uv_max)


def best_windows(points: Points, max_uv: float = 2.0) -> list[tuple[datetime, datetime]]:
    """Intervalos contínuos com UV <= `max_uv`. O chamador já filtra as horas (6h–19h)."""
    windows: list[tuple[datetime, datetime]] = []
    start: datetime | None = None
    previous: datetime | None = None
    for time, uv in points:
        if uv <= max_uv:
            if start is None:
                start = time
            previous = time
        elif start is not None:
            windows.append((start, previous + HOUR))
            start = None
    if start is not None:
        windows.append((start, previous + HOUR))
    return windows


def hours_at_or_above(points: Points, threshold: float = 8.0) -> int:
    return sum(1 for _, uv in points if uv >= threshold)
