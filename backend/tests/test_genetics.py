from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.genetics.burn import minutes_to_burn
from app.genetics.seed import seed_genetics
from app.seed.cities import seed_cities
from tests.conftest import FIXED_NOW
from tests.factories import add_hourly, add_reading

SP = ZoneInfo("America/Sao_Paulo")


def test_minutes_to_burn_type_ii_uv10():
    assert minutes_to_burn(10, 250) == 17


def test_minutes_to_burn_none_at_night():
    assert minutes_to_burn(0, 250) is None
    assert minutes_to_burn(0.4, 250) is None


def test_phototypes_listed_with_source(client, session):
    seed_cities(session)
    seed_genetics(session)
    body = client.get("/api/v1/phototypes").json()
    assert [p["code"] for p in body] == ["I", "II", "III", "IV", "V", "VI"]
    assert body[1]["med_j_m2"] == 250
    assert "Fitzpatrick" in body[0]["source"]


def test_current_with_phototype(client, session):
    seed_cities(session)
    seed_genetics(session)
    add_reading(session, 1, FIXED_NOW - timedelta(minutes=5), 10)
    body = client.get("/api/v1/cities/1/current", params={"phototype": "II"}).json()
    assert body["minutes_to_burn"] == 17
    assert client.get("/api/v1/cities/1/current").json()["minutes_to_burn"] is None
    assert client.get("/api/v1/cities/1/current", params={"phototype": "VII"}).status_code == 422


def test_compare_vulnerability_curitiba(client, session):
    seed_cities(session)
    seed_genetics(session)
    curitiba = 4
    add_hourly(session, curitiba, datetime(2026, 11, 18, 12, tzinfo=SP).astimezone(UTC), 9)
    rows = client.get("/api/v1/compare").json()["rows"]
    row = next(r for r in rows if r["city"]["id"] == curitiba)
    assert row["vulnerability"] == 6.3
    assert row["vulnerability_illustrative"] is True


def test_seed_genetics_is_idempotent(session):
    from app.genetics.models import CityPhototypeDistribution, SkinPhototype

    seed_cities(session)
    seed_genetics(session)
    seed_genetics(session)
    assert session.query(SkinPhototype).count() == 6
    assert session.query(CityPhototypeDistribution).count() == 30
