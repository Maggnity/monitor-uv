from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.seed.cities import seed_cities
from tests.conftest import FIXED_NOW
from tests.factories import add_daily, add_hourly, add_reading, city

SP = ZoneInfo("America/Sao_Paulo")


def sp_hour(hour: int, day: int = 18) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=SP).astimezone(UTC)


def test_cities_autocomplete_ignores_accents(client, session):
    seed_cities(session)
    names = [c["name"] for c in client.get("/api/v1/cities", params={"q": "sao"}).json()]
    assert names == ["São Paulo"]


def test_nearest_city(client, session):
    seed_cities(session)
    response = client.get("/api/v1/cities/nearest", params={"lat": -3.8, "lng": -38.5})
    assert response.json()["name"] == "Fortaleza"


def test_current_no_data_returns_200(client, session):
    seed_cities(session)
    response = client.get("/api/v1/cities/1/current")
    assert response.status_code == 200
    assert response.json()["status"] == "no_data"
    assert response.json()["level"] is None


def test_current_measured(client, session):
    seed_cities(session)
    add_reading(session, city(session).id, FIXED_NOW - timedelta(minutes=10), 9)
    body = client.get("/api/v1/cities/1/current").json()
    assert body["status"] == "ok"
    assert body["display_kind"] == "measured"
    assert body["display_uv"] == 9
    assert body["level"] == {
        "key": "very_high",
        "label": "Muito alto",
        "recommendation": "Evite sol entre 10h e 16h",
    }


def test_current_estimated_interpolates_forecast(client, session):
    seed_cities(session)
    add_hourly(session, 1, sp_hour(14), 9.0)
    add_hourly(session, 1, sp_hour(15), 7.0)
    body = client.get("/api/v1/cities/1/current").json()
    assert body["display_kind"] == "estimated"
    assert body["estimated_uv"] == 9.0


def test_current_night_includes_tomorrow_peak(client, session, clock):
    seed_cities(session)
    clock["now"] = sp_hour(22)
    add_hourly(session, 1, sp_hour(22), 0)
    for hour, uv in [(11, 10.0), (12, 11.0), (13, 10.5), (14, 8)]:
        add_hourly(session, 1, sp_hour(hour, day=19), uv)
    body = client.get("/api/v1/cities/1/current").json()
    assert body["status"] == "night"
    assert body["next_peak"]["date"] == "2026-11-19"
    assert body["next_peak"]["uv_max"] == 11.0


def test_today_returns_peak_and_best_windows(client, session):
    seed_cities(session)
    curve = [0.5, 1.8, 3, 5, 7, 9, 10, 9, 7, 5, 3, 2.5, 1.2, 0.3]
    for i, uv in enumerate(curve):
        add_hourly(session, 1, sp_hour(6 + i), uv)
    add_hourly(session, 1, sp_hour(3), 0)  # fora de 6h–19h
    body = client.get("/api/v1/cities/1/today").json()
    assert body["kind"] == "forecast"
    assert body["date"] == "2026-11-18"
    assert len(body["hourly"]) == 14
    assert body["peak"]["uv_max"] == 10
    assert body["hours_above_8"] == 3
    assert len(body["best_windows"]) == 2


def test_forecast_returns_five_days_with_level(client, session):
    seed_cities(session)
    for offset in range(6):
        add_daily(session, 1, date(2026, 11, 18) + timedelta(days=offset), 8 + offset)
    body = client.get("/api/v1/cities/1/forecast").json()
    assert len(body) == 5
    assert body[0]["date"] == "2026-11-18"
    assert body[0]["level"]["key"] == "very_high"


def test_unknown_city_404(client, session):
    seed_cities(session)
    response = client.get("/api/v1/cities/999/current")
    assert response.status_code == 404
    assert response.json() == {"detail": "Cidade não encontrada"}


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok", "database": "ok"}
