"""Tipos comuns aos provedores de dados de UV."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

import httpx


class CityLike(Protocol):
    lat: float
    lng: float
    timezone: str
    station_code: str


@dataclass(frozen=True)
class CurrentReading:
    measured_at: datetime
    uv: float
    uv_max: float | None
    uv_max_at: datetime | None
    source: str


@dataclass(frozen=True)
class HourlyPoint:
    forecast_for: datetime
    uv: float


@dataclass(frozen=True)
class DailyPoint:
    date: date
    uv_max: float
    weather_code: int | None


@dataclass(frozen=True)
class Forecast:
    hourly: list[HourlyPoint]
    daily: list[DailyPoint]
    source: str


class ProviderError(Exception):
    """Falha ao consultar um provedor externo (rede, autenticação, cota)."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class CurrentProvider(Protocol):
    source: str

    def fetch_current(self, city: CityLike, now_utc: datetime | None = None) -> CurrentReading: ...


class ForecastProvider(Protocol):
    source: str

    def fetch_forecast(self, city: CityLike, now_utc: datetime | None = None) -> Forecast: ...


RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 0.5


def get_with_retry(
    client: httpx.Client,
    url: str,
    *,
    params: dict,
    headers: dict | None = None,
    name: str,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """GET com retry e backoff exponencial em erro de rede ou 5xx.

    Erros de autenticação e cota (4xx) não são repetidos: tentar de novo só gasta cota.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            response = client.get(url, params=params, headers=headers, timeout=15)
        except httpx.TransportError as exc:
            if attempt == RETRY_ATTEMPTS:
                raise ProviderError(f"Falha de rede em {name}: {exc}") from exc
        else:
            if response.status_code < 500:
                if response.status_code != 200:
                    raise ProviderError(
                        f"{name} respondeu {response.status_code}", status=response.status_code
                    )
                return response
            if attempt == RETRY_ATTEMPTS:
                raise ProviderError(
                    f"{name} respondeu {response.status_code}", status=response.status_code
                )
        sleep(RETRY_BACKOFF_SECONDS * 2 ** (attempt - 1))
    raise AssertionError("inalcançável")
