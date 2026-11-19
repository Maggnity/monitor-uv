from app.models import City
from app.seed.cities import seed_cities


def test_seed_cities_is_idempotent(session):
    seed_cities(session)
    seed_cities(session)
    assert session.query(City).count() == 5
    fortaleza = session.query(City).filter_by(station_code="FOR-01").one()
    assert fortaleza.timezone == "America/Fortaleza"
