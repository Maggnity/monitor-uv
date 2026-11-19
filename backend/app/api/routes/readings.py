from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.api.schemas import ReadingOut, ReadingsPage
from app.models import UvReading

router = APIRouter(prefix="/readings", tags=["Leituras"])


@router.get("", response_model=ReadingsPage, summary="Consulta paginada das leituras gravadas")
def list_readings(
    session: SessionDep,
    city_id: int | None = Query(None),
    from_: datetime | None = Query(None, alias="from", description="Início (ISO 8601)"),
    to: datetime | None = Query(None, description="Fim, exclusivo (ISO 8601)"),
    origin: Literal["real", "sintetico"] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = []
    if city_id is not None:
        filters.append(UvReading.city_id == city_id)
    if from_ is not None:
        filters.append(UvReading.measured_at >= from_)
    if to is not None:
        filters.append(UvReading.measured_at < to)
    if origin is not None:
        filters.append(UvReading.origin == origin)

    total = session.scalar(select(func.count()).select_from(UvReading).where(*filters))
    rows = session.scalars(
        select(UvReading)
        .where(*filters)
        .order_by(UvReading.measured_at.desc(), UvReading.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return ReadingsPage(
        items=[
            ReadingOut(
                id=r.id,
                city_id=r.city_id,
                measured_at=r.measured_at,
                uv_index=float(r.uv_index),
                source=r.source,
                origin=r.origin,
            )
            for r in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )
