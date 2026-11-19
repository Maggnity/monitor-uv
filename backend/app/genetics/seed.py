"""Dados de referência da camada genética. Idempotente.

MED por fototipo: valores típicos citados na literatura de fotobiologia
(Fitzpatrick, 1988; Diffey, 1991). A distribuição por cidade é ILUSTRATIVA, criada para a
demonstração: não existe base pública com fototipo por município.
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.genetics.models import CityPhototypeDistribution, SkinPhototype
from app.models import City

MED_SOURCE = "Valores típicos citados na literatura (Fitzpatrick, 1988; Diffey, 1991)"
DISTRIBUTION_SOURCE = "Distribuição ilustrativa para demonstração (não é dado censitário)"

PHOTOTYPES = [
    ("I", "Pele muito clara: sempre queima, nunca bronzeia", 200),
    ("II", "Pele clara: queima com facilidade, bronzeia pouco", 250),
    ("III", "Pele morena clara: às vezes queima, bronzeia aos poucos", 300),
    ("IV", "Pele morena: raramente queima, bronzeia com facilidade", 450),
    ("V", "Pele morena escura: muito raramente queima", 600),
    ("VI", "Pele negra: nunca queima", 1000),
]

CODES = [code for code, _, _ in PHOTOTYPES]

DISTRIBUTION = {
    "SP-01": (0.05, 0.20, 0.30, 0.25, 0.15, 0.05),
    "RJ-01": (0.03, 0.15, 0.30, 0.27, 0.18, 0.07),
    "BH-01": (0.03, 0.15, 0.30, 0.27, 0.18, 0.07),
    "CWB-01": (0.08, 0.30, 0.32, 0.18, 0.09, 0.03),
    "FOR-01": (0.02, 0.10, 0.25, 0.33, 0.22, 0.08),
}


def seed_genetics(session: Session) -> None:
    stmt = insert(SkinPhototype).values(
        [
            {"code": code, "description": desc, "med_j_m2": med, "source": MED_SOURCE}
            for code, desc, med in PHOTOTYPES
        ]
    )
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=[SkinPhototype.code],
            set_={c: stmt.excluded[c] for c in ("description", "med_j_m2", "source")},
        )
    )
    rows = []
    for city in session.query(City):
        shares = DISTRIBUTION.get(city.station_code)
        if not shares:
            continue
        rows.extend(
            {
                "city_id": city.id,
                "phototype": code,
                "share": share,
                "source": DISTRIBUTION_SOURCE,
                "is_illustrative": True,
            }
            for code, share in zip(CODES, shares, strict=True)
        )
    if rows:
        stmt = insert(CityPhototypeDistribution).values(rows)
        session.execute(
            stmt.on_conflict_do_update(
                index_elements=[
                    CityPhototypeDistribution.city_id,
                    CityPhototypeDistribution.phototype,
                ],
                set_={"share": stmt.excluded.share, "source": stmt.excluded.source},
            )
        )
    session.commit()
