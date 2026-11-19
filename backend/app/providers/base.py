"""Tipos comuns aos provedores de dados de UV."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


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
