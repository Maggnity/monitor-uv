"""Conversões entre UTC e o horário local de cada cidade."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def local_now(now_utc: datetime, tz: str) -> datetime:
    return now_utc.astimezone(ZoneInfo(tz))


def local_date(dt_utc: datetime, tz: str) -> date:
    return dt_utc.astimezone(ZoneInfo(tz)).date()


def local_day_bounds_utc(d: date, tz: str) -> tuple[datetime, datetime]:
    """Início (inclusive) e fim (exclusivo) do dia local `d`, em UTC."""
    zone = ZoneInfo(tz)
    start = datetime.combine(d, time.min, tzinfo=zone)
    end = datetime.combine(d + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(ZoneInfo("UTC")), end.astimezone(ZoneInfo("UTC"))
