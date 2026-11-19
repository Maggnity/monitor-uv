"""Cliente da Open-Meteo: previsão horária e diária de UV (não exige chave)."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import httpx

from app.providers.base import CityLike, DailyPoint, Forecast, HourlyPoint, ProviderError

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoProvider:
    source = "openmeteo"

    def __init__(self, client: httpx.Client):
        self._client = client

    def fetch_forecast(self, city: CityLike, now_utc: datetime | None = None) -> Forecast:
        try:
            response = self._client.get(
                OPENMETEO_URL,
                params={
                    "latitude": float(city.lat),
                    "longitude": float(city.lng),
                    "hourly": "uv_index",
                    "daily": "uv_index_max,weather_code",
                    "timezone": city.timezone,
                    "forecast_days": 5,
                },
                timeout=15,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Falha de rede na Open-Meteo: {exc}") from exc
        if response.status_code != 200:
            raise ProviderError(
                f"Open-Meteo respondeu {response.status_code}", status=response.status_code
            )
        body = response.json()
        zone = ZoneInfo(city.timezone)
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
