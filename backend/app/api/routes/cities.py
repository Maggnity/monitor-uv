from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CityDep, NowDep, SessionDep, SettingsDep
from app.api.schemas import (
    CityOut,
    CurrentOut,
    ForecastDayOut,
    HistoryDayOut,
    HistoryOut,
    HourlyOut,
    LevelOut,
    PeakOut,
    PeakWindowOut,
    TodayOut,
    WindowOut,
)
from app.domain.uv_scale import classify
from app.genetics.burn import minutes_to_burn
from app.genetics.service import med_for
from app.services import cities as service
from app.services.compare import history as history_service

router = APIRouter(prefix="/cities", tags=["Cidades"])


@router.get("", response_model=list[CityOut], summary="Lista cidades (com busca por nome)")
def list_cities(
    session: SessionDep,
    q: str | None = Query(None, description="Trecho do nome, sem diferenciar acentos"),
):
    return service.search_cities(session, q)


@router.get("/nearest", response_model=CityOut, summary="Cidade monitorada mais próxima")
def nearest(
    session: SessionDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    city = service.nearest_city(session, lat, lng)
    if city is None:
        raise HTTPException(status_code=404, detail="Nenhuma cidade cadastrada")
    return city


@router.get("/{city_id}/current", response_model=CurrentOut, summary="UV agora")
def current(
    city: CityDep,
    session: SessionDep,
    now: NowDep,
    settings: SettingsDep,
    phototype: Literal["I", "II", "III", "IV", "V", "VI"] | None = Query(
        None, description="Fototipo de Fitzpatrick para estimar o tempo até queimar"
    ),
):
    state, peak = service.current_for_city(session, city, now, settings)
    burn = None
    if phototype and state.display_uv is not None:
        med = med_for(session, phototype)
        burn = minutes_to_burn(state.display_uv, med) if med else None
    return CurrentOut(
        city=CityOut.model_validate(city),
        status=state.status,
        display_uv=state.display_uv,
        display_kind=state.display_kind,
        measured_uv=state.measured_uv,
        measured_at=state.measured_at,
        estimated_uv=state.estimated_uv,
        level=LevelOut.of(state.level),
        next_peak=PeakOut(**peak.__dict__) if peak else None,
        minutes_to_burn=burn,
    )


@router.get("/{city_id}/today", response_model=TodayOut, summary="Linha do tempo de hoje (6h–19h)")
def today(city: CityDep, session: SessionDep, now: NowDep):
    view = service.today_for_city(session, city, now)
    return TodayOut(
        date=view.date,
        hourly=[HourlyOut(time=t, uv=uv, level_key=classify(uv).key) for t, uv in view.points],
        peak=PeakWindowOut(**view.peak.__dict__) if view.peak else None,
        best_windows=[WindowOut(start=s, end=e) for s, e in view.best],
        hours_above_8=view.hours_above_8,
    )


@router.get(
    "/{city_id}/forecast", response_model=list[ForecastDayOut], summary="Previsão de 5 dias"
)
def forecast(city: CityDep, session: SessionDep, now: NowDep):
    return [
        ForecastDayOut(
            date=day.date,
            uv_max=float(day.uv_max),
            level=LevelOut.of(classify(float(day.uv_max))),
            weather_code=day.weather_code,
        )
        for day in service.forecast_for_city(session, city, now)
    ]


@router.get(
    "/{city_id}/history", response_model=HistoryOut, summary="Histórico de UV máximo diário"
)
def history(
    city: CityDep,
    session: SessionDep,
    now: NowDep,
    period: Literal["7d", "30d", "12m"] = Query("7d", description="7d, 30d ou 12m"),
):
    days = history_service(session, city, now, period)
    return HistoryOut(
        period=period,
        contains_synthetic=any(d.origin == "sintetico" for d in days),
        days=[
            HistoryDayOut(
                date=d.date, uv_max=d.uv_max, level_key=classify(d.uv_max).key, origin=d.origin
            )
            for d in days
        ],
    )
