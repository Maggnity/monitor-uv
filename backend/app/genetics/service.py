"""Consultas da camada genética."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.genetics.burn import SENSITIVE_PHOTOTYPES
from app.genetics.models import CityPhototypeDistribution, SkinPhototype


def list_phototypes(session: Session) -> list[SkinPhototype]:
    order = {code: i for i, code in enumerate(("I", "II", "III", "IV", "V", "VI"))}
    return sorted(session.scalars(select(SkinPhototype)), key=lambda p: order.get(p.code, 99))


def med_for(session: Session, code: str) -> int | None:
    phototype = session.get(SkinPhototype, code)
    return phototype.med_j_m2 if phototype else None


def sensitive_share_by_city(session: Session) -> dict[int, float]:
    rows = session.execute(
        select(CityPhototypeDistribution.city_id, func.sum(CityPhototypeDistribution.share))
        .where(CityPhototypeDistribution.phototype.in_(SENSITIVE_PHOTOTYPES))
        .group_by(CityPhototypeDistribution.city_id)
    )
    return {city_id: float(total) for city_id, total in rows}
