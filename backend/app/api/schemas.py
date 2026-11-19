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


class HistoryDayOut(BaseModel):
    date: date
    uv_max: float
    level_key: str
    origin: Literal["real", "sintetico", "forecast"]


class HistoryOut(BaseModel):
    period: Literal["7d", "30d", "12m"]
    contains_synthetic: bool = Field(description="O período inclui dias sintéticos de demonstração")
    days: list[HistoryDayOut]


class CompareRowOut(BaseModel):
    city: CityOut
    current_uv: float | None
    current_kind: Literal["measured", "estimated"] | None
    peak_today: float | None = Field(description="Pico previsto para hoje")
    hours_above_8: int = Field(description="Horas previstas hoje com UV >= 8")
    trend: Literal["up", "down", "stable"] = Field(
        description="Pico de hoje comparado à média dos 7 dias anteriores"
    )
    sparkline: list[float] = Field(description="UV máximo dos 7 dias anteriores + hoje")


class SeriesPointOut(BaseModel):
    time: datetime
    uv: float


class SeriesOut(BaseModel):
    city_id: int
    points: list[SeriesPointOut]


class CompareOut(BaseModel):
    date: date
    contains_synthetic: bool
    rows: list[CompareRowOut]
    series: list[SeriesOut]


class MapPointOut(BaseModel):
    city_id: int
    name: str
    lat: float
    lng: float
    uv: float | None
    level: LevelOut | None
    kind: Literal["measured", "estimated", "forecast"] | None


class AlertCreate(BaseModel):
    city_id: int
    threshold: float = Field(ge=1, le=15, description="Avisar quando o UV passar deste valor")


class AlertUpdate(BaseModel):
    active: bool | None = None
    threshold: float | None = Field(default=None, ge=1, le=15)


class AlertOut(BaseModel):
    id: int
    city: CityOut
    threshold: float
    active: bool
    created_at: datetime
    last_triggered_at: datetime | None


class AlertTriggerOut(BaseModel):
    alert_id: int
    city_id: int
    city_name: str
    threshold: float
    uv: float
    triggered_at: datetime


class ReadingOut(BaseModel):
    id: int
    city_id: int
    measured_at: datetime
    uv_index: float
    source: str
    origin: Literal["real", "sintetico"]


class ReadingsPage(BaseModel):
    items: list[ReadingOut]
    page: int
    page_size: int
    total: int
