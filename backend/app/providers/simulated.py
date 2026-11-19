"""Provedor simulado: gera UV com a curva em sino, sem rede nem chave."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.synthetic import PEAK_BASE, PEAK_HOUR, bell_uv, day_rng, seasonal_peak
from app.providers.base import CityLike, CurrentReading, DailyPoint, Forecast, HourlyPoint

WEATHER_CODES = (0, 1, 2, 3)


class SimulatedProvider:
    source = "simulado"

    def _peak(self, city: CityLike, local_day) -> float:
        rng = day_rng(city.station_code, local_day)
        return seasonal_peak(PEAK_BASE.get(city.station_code, 10), float(city.lat), local_day, rng)

    def fetch_current(self, city: CityLike, now_utc: datetime | None = None) -> CurrentReading:
        now_utc = now_utc or datetime.now(UTC)
        measured_at = now_utc.replace(
            minute=now_utc.minute - now_utc.minute % 10, second=0, microsecond=0
        )
        local = measured_at.astimezone(ZoneInfo(city.timezone))
        peak = self._peak(city, local.date())
        hour = local.hour + local.minute / 60
        peak_at = local.replace(hour=12, minute=15, second=0, microsecond=0)
        return CurrentReading(
            measured_at=measured_at,
            uv=bell_uv(hour, peak),
            uv_max=bell_uv(PEAK_HOUR, peak),
            uv_max_at=peak_at.astimezone(UTC),
            source=self.source,
        )

    def fetch_forecast(self, city: CityLike, now_utc: datetime | None = None) -> Forecast:
        now_utc = now_utc or datetime.now(UTC)
        zone = ZoneInfo(city.timezone)
        today = now_utc.astimezone(zone).date()
        hourly: list[HourlyPoint] = []
        daily: list[DailyPoint] = []
        for offset in range(5):
            day = today + timedelta(days=offset)
            peak = self._peak(city, day)
            for hour in range(24):
                local = datetime(day.year, day.month, day.day, hour, tzinfo=zone)
                hourly.append(HourlyPoint(local.astimezone(UTC), bell_uv(hour, peak)))
            weather = day_rng(city.station_code, day).choice(WEATHER_CODES)
            daily.append(DailyPoint(day, bell_uv(PEAK_HOUR, peak), weather))
        return Forecast(hourly=hourly, daily=daily, source=self.source)
