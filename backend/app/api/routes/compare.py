import csv
import io
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import NowDep, SessionDep, SettingsDep
from app.api.schemas import CityOut, CompareOut, CompareRowOut, SeriesOut, SeriesPointOut
from app.genetics.burn import vulnerability
from app.genetics.service import sensitive_share_by_city
from app.models import City
from app.services import compare as service
from app.timeutil import local_now

router = APIRouter(prefix="/compare", tags=["Comparação"])

MAX_SERIES = 4
REFERENCE_TZ = "America/Sao_Paulo"
TREND_LABEL = {"up": "subindo", "down": "caindo", "stable": "estável"}


def _parse_ids(raw: str | None, session) -> list[City]:
    cities = list(session.scalars(select(City).order_by(City.id)))
    if not raw:
        return cities[:MAX_SERIES]
    try:
        ids = [int(part) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise HTTPException(
            422, "city_ids deve ser uma lista de números separados por vírgula"
        ) from exc
    if len(ids) > MAX_SERIES:
        raise HTTPException(422, f"Compare no máximo {MAX_SERIES} cidades no gráfico")
    by_id = {c.id: c for c in cities}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise HTTPException(404, "Cidade não encontrada")
    return [by_id[i] for i in ids]


def _decimal(value: float | None) -> str:
    """Número no formato do Excel pt-BR (vírgula decimal)."""
    return "" if value is None else str(value).replace(".", ",")


CityIds = Annotated[
    str | None,
    Query(description="Até 4 ids separados por vírgula para o gráfico (padrão: os 4 primeiros)"),
]
DateParam = Annotated[date | None, Query(description="Dia do gráfico (padrão: hoje)")]


@router.get("", response_model=CompareOut, summary="Compara cidades: tabela e séries por hora")
def compare(
    session: SessionDep,
    now: NowDep,
    settings: SettingsDep,
    city_ids: CityIds = None,
    date: DateParam = None,
):
    selected = _parse_ids(city_ids, session)
    day = date or local_now(now, REFERENCE_TZ).date()
    rows = [
        service.compare_row(session, city, now, settings)
        for city in session.scalars(select(City).order_by(City.id))
    ]
    shares = sensitive_share_by_city(session)
    series: list[SeriesOut] = []
    series_synthetic = False
    for city in selected:
        points, synthetic = service.day_series(session, city, day, now)
        series_synthetic |= synthetic
        series.append(
            SeriesOut(city_id=city.id, points=[SeriesPointOut(time=t, uv=uv) for t, uv in points])
        )
    return CompareOut(
        date=day,
        contains_synthetic=series_synthetic or any(r.has_synthetic for r in rows),
        rows=[
            CompareRowOut(
                city=CityOut.model_validate(r.city),
                current_uv=r.current_uv,
                current_kind=r.current_kind,
                current_synthetic=r.current_synthetic,
                peak_today=r.peak_today,
                hours_above_8=r.hours_above_8,
                trend=r.trend,
                sparkline=r.sparkline,
                vulnerability=vulnerability(r.peak_today, shares.get(r.city.id)),
                vulnerability_illustrative=r.city.id in shares,
            )
            for r in rows
        ],
        series=series,
    )


@router.get(
    "/export.csv",
    summary="Exporta a tabela comparativa de hoje em CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_csv(session: SessionDep, now: NowDep, settings: SettingsDep):
    day = local_now(now, REFERENCE_TZ).date()
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(
        [
            "cidade",
            "uf",
            "data",
            "uv_atual",
            "tipo_uv_atual",
            "pico_previsto",
            "horas_acima_de_8",
            "tendencia",
            "vulnerabilidade_estimada_ilustrativa",
        ]
    )
    shares = sensitive_share_by_city(session)
    for city in session.scalars(select(City).order_by(City.id)):
        row = service.compare_row(session, city, now, settings)
        estimated = vulnerability(row.peak_today, shares.get(city.id))
        writer.writerow(
            [
                city.name,
                city.state,
                day.isoformat(),
                _decimal(row.current_uv),
                {"measured": "medido", "estimated": "estimado"}.get(row.current_kind, ""),
                _decimal(row.peak_today),
                row.hours_above_8,
                TREND_LABEL[row.trend],
                _decimal(estimated),
            ]
        )
    # BOM para o Excel reconhecer UTF-8 (acentos); `;` e vírgula decimal = padrão pt-BR.
    return Response(
        content="﻿" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="comparativo-uv-{day}.csv"'},
    )
