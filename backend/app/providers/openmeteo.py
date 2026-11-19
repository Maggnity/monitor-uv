"""Cliente da Open-Meteo: previsão horária e diária de UV (não exige chave)."""

import time
from collections.abc import Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import httpx

from app.providers.base import (
    CityLike,
    DailyPoint,
    Forecast,
    HourlyPoint,
    ProviderError,
    get_with_retry,
)

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoProvider:
    source = "openmeteo"

    def __init__(self, client: httpx.Client, sleep: Callable[[float], None] = time.sleep):
        self._client = client
        self._sleep = sleep

    def fetch_forecast(self, city: CityLike, now_utc: datetime | None = None) -> Forecast:
        response = get_with_retry(
            self._client,
            OPENMETEO_URL,
            params={
                "latitude": float(city.lat),
                "longitude": float(city.lng),
                "hourly": "uv_index",
                "daily": "uv_index_max,weather_code",
                "timezone": city.timezone,
                "forecast_days": 5,
            },
            name="Open-Meteo",
            sleep=self._sleep,
        )
        try:
            return self._parse(response.json(), ZoneInfo(city.timezone))
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Resposta inesperada da Open-Meteo: {exc}") from exc

    def _parse(self, body: dict, zone: ZoneInfo) -> Forecast:
        hourly = [
            HourlyPoint(
                forecast_for=datetime.fromisoformat(t).replace(tzinfo=zone).astimezone(UTC),
                uv=float(uv),
            )
            for t, uv in zip(body["hourly"]["time"], body["hourly"]["uv_index"], strict=True)
            if uv is not None
        ]
        daily_body = body["daily"]
        daily = [
            DailyPoint(date=date.fromisoformat(d), uv_max=float(uv), weather_code=code)
            for d, uv, code in zip(
                daily_body["time"],
                daily_body["uv_index_max"],
                daily_body.get("weather_code", [None] * len(daily_body["time"])),
                strict=True,
            )
            if uv is not None
        ]
        return Forecast(hourly=hourly, daily=daily, source=self.source)
