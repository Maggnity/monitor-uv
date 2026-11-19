"""Tabelas da camada genética: fototipos de pele e distribuição ilustrativa por cidade."""

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SkinPhototype(Base):
    """Fototipo de Fitzpatrick (I–VI) e a dose eritematosa mínima (MED) típica."""

    __tablename__ = "skin_phototype"
    __table_args__ = (CheckConstraint("med_j_m2 > 0", name="ck_phototype_med_positive"),)

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    description: Mapped[str] = mapped_column(String(120))
    med_j_m2: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(200))


class CityPhototypeDistribution(Base):
    """Proporção estimada da população de cada fototipo. Valores ILUSTRATIVOS."""

    __tablename__ = "city_phototype_distribution"
    __table_args__ = (
        CheckConstraint("share >= 0 AND share <= 1", name="ck_distribution_share_range"),
    )

    city_id: Mapped[int] = mapped_column(
        ForeignKey("city.id", ondelete="CASCADE"), primary_key=True
    )
    phototype: Mapped[str] = mapped_column(
        ForeignKey("skin_phototype.code", ondelete="CASCADE"), primary_key=True
    )
    share: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    source: Mapped[str] = mapped_column(String(200))
    is_illustrative: Mapped[bool] = mapped_column(Boolean, default=True)
