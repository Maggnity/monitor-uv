"""Cadastro das cidades monitoradas (uma estação por cidade)."""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import City

CITIES: list[dict] = [
    {
        "name": "São Paulo",
        "state": "SP",
        "lat": -23.5505,
        "lng": -46.6333,
        "timezone": "America/Sao_Paulo",
        "station_code": "SP-01",
    },
    {
        "name": "Rio de Janeiro",
        "state": "RJ",
        "lat": -22.9068,
        "lng": -43.1729,
        "timezone": "America/Sao_Paulo",
        "station_code": "RJ-01",
    },
    {
        "name": "Belo Horizonte",
        "state": "MG",
        "lat": -19.9167,
        "lng": -43.9345,
        "timezone": "America/Sao_Paulo",
        "station_code": "BH-01",
    },
    {
        "name": "Curitiba",
        "state": "PR",
        "lat": -25.4284,
        "lng": -49.2733,
        "timezone": "America/Sao_Paulo",
        "station_code": "CWB-01",
    },
    {
        "name": "Fortaleza",
        "state": "CE",
        "lat": -3.7319,
        "lng": -38.5267,
        "timezone": "America/Fortaleza",
        "station_code": "FOR-01",
    },
]


def seed_cities(session: Session) -> int:
    """Insere ou atualiza as cidades pelo código da estação. Idempotente."""
    stmt = insert(City).values(CITIES)
    stmt = stmt.on_conflict_do_update(
        index_elements=[City.station_code],
        set_={c: stmt.excluded[c] for c in ("name", "state", "lat", "lng", "timezone")},
    )
    session.execute(stmt)
    session.commit()
    return session.query(City).count()
