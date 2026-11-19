"""Modelos de resposta da API (documentados no Swagger)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.uv_scale import UvLevel


class LevelOut(BaseModel):
    key: Literal["low", "moderate", "high", "very_high", "extreme"]
    label: str = Field(examples=["Muito alto"])
    recommendation: str = Field(examples=["Evite sol entre 10h e 16h"])

    @classmethod
    def of(cls, level: UvLevel | None) -> "LevelOut | None":
        if level is None:
            return None
        return cls(key=level.key, label=level.label, recommendation=level.recommendation)


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(examples=["São Paulo"])
    state: str = Field(examples=["SP"])
    lat: float
    lng: float
    timezone: str = Field(examples=["America/Sao_Paulo"])
    station_code: str = Field(examples=["SP-01"])


class PeakOut(BaseModel):
    date: date
    uv_max: float
    start: datetime | None = None
    end: datetime | None = None


class CurrentOut(BaseModel):
    city: CityOut
    status: Literal["ok", "stale", "night", "no_data"] = Field(
        description="ok | stale (estação sem leitura recente) | night | no_data"
    )
    display_uv: float | None = Field(description="Valor a exibir como 'UV agora'")
    display_kind: Literal["measured", "estimated"] | None = Field(
        description="measured = medição real; estimated = previsão para a hora atual"
    )
    measured_uv: float | None
    measured_at: datetime | None
    estimated_uv: float | None
    level: LevelOut | None
    next_peak: PeakOut | None = Field(
        default=None, description="Próximo pico previsto (preenchido à noite)"
    )


class HourlyOut(BaseModel):
    time: datetime
    uv: float
    level_key: str


class WindowOut(BaseModel):
    start: datetime
    end: datetime


class PeakWindowOut(BaseModel):
    start: datetime
    end: datetime
    uv_max: float


class TodayOut(BaseModel):
    date: date
    hourly: list[HourlyOut]
    peak: PeakWindowOut | None
    best_windows: list[WindowOut] = Field(description="Intervalos com UV <= 2 entre 6h e 19h")
    hours_above_8: int
    kind: Literal["forecast"] = "forecast"


class ForecastDayOut(BaseModel):
    date: date
    uv_max: float
    level: LevelOut
    weather_code: int | None


class HealthOut(BaseModel):
    status: str
    database: str
