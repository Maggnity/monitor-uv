from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import NowDep, SessionDep, SettingsDep
from app.api.schemas import LevelOut, MapPointOut
from app.domain.uv_scale import classify
from app.models import City
from app.services.compare import map_points

router = APIRouter(prefix="/map", tags=["Mapa"])


@router.get("", response_model=list[MapPointOut], summary="UV de todas as cidades para o mapa")
def city_map(
    session: SessionDep,
    now: NowDep,
    settings: SettingsDep,
    when: Literal["now", "peak_today", "tomorrow"] = Query(
        "now", description="now = agora; peak_today = pico previsto hoje; tomorrow = pico de amanhã"
    ),
):
    cities = list(session.scalars(select(City).order_by(City.id)))
    return [
        MapPointOut(
            city_id=p.city.id,
            name=p.city.name,
            lat=float(p.city.lat),
            lng=float(p.city.lng),
            uv=p.uv,
            level=LevelOut.of(classify(p.uv)) if p.uv is not None else None,
            kind=p.kind if p.uv is not None else None,
        )
        for p in map_points(session, cities, now, settings, when)
    ]
