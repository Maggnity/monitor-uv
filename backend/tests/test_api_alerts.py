import uuid
from datetime import UTC, datetime, timedelta

from app.models import Alert, AlertTrigger
from app.seed.cities import seed_cities
from app.services.alerts import evaluate_alerts
from tests.factories import add_reading, city

CLIENT_A = str(uuid.uuid4())
CLIENT_B = str(uuid.uuid4())


def headers(client_id: str) -> dict:
    return {"X-Client-Id": client_id}


def test_alerts_require_client_id(client, session):
    seed_cities(session)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 400
    assert response.json() == {"detail": "Header X-Client-Id obrigatório"}
    assert client.get("/api/v1/alerts", headers=headers("abc")).status_code == 400


def test_alert_threshold_out_of_range(client, session):
    seed_cities(session)
    for threshold in (0, 16):
        response = client.post(
            "/api/v1/alerts", json={"city_id": 1, "threshold": threshold}, headers=headers(CLIENT_A)
        )
        assert response.status_code == 422


def test_alert_unknown_city_404(client, session):
    seed_cities(session)
    response = client.post(
        "/api/v1/alerts", json={"city_id": 99, "threshold": 8}, headers=headers(CLIENT_A)
    )
    assert response.status_code == 404


def test_alert_crud(client, session):
    seed_cities(session)
    created = client.post(
        "/api/v1/alerts", json={"city_id": 5, "threshold": 8}, headers=headers(CLIENT_A)
    )
    assert created.status_code == 201
    alert_id = created.json()["id"]
    assert created.json()["city"]["name"] == "Fortaleza"
    assert created.json()["active"] is True

    patched = client.patch(
        f"/api/v1/alerts/{alert_id}", json={"active": False}, headers=headers(CLIENT_A)
    )
    assert patched.json()["active"] is False

    assert len(client.get("/api/v1/alerts", headers=headers(CLIENT_A)).json()) == 1
    deleted = client.delete(f"/api/v1/alerts/{alert_id}", headers=headers(CLIENT_A))
    assert deleted.status_code == 204
    assert client.get("/api/v1/alerts", headers=headers(CLIENT_A)).json() == []


def test_alerts_isolated_by_client(client, session):
    seed_cities(session)
    alert_id = client.post(
        "/api/v1/alerts", json={"city_id": 1, "threshold": 8}, headers=headers(CLIENT_A)
    ).json()["id"]
    assert client.get("/api/v1/alerts", headers=headers(CLIENT_B)).json() == []
    response = client.patch(
        f"/api/v1/alerts/{alert_id}", json={"active": False}, headers=headers(CLIENT_B)
    )
    assert response.status_code == 404


def test_evaluate_alerts_once_per_day(session):
    seed_cities(session)
    sp = city(session)
    session.add(Alert(client_id=uuid.UUID(CLIENT_A), city_id=sp.id, threshold=8, active=True))
    session.flush()
    noon = datetime(2026, 11, 18, 15, 0, tzinfo=UTC)
    at_threshold = add_reading(session, sp.id, noon - timedelta(hours=2), 8)
    assert evaluate_alerts(session, at_threshold, sp) == 0
    first = add_reading(session, sp.id, noon, 9)
    second = add_reading(session, sp.id, noon + timedelta(hours=2), 10)
    assert evaluate_alerts(session, first, sp) == 1
    assert evaluate_alerts(session, second, sp) == 0
    assert session.query(AlertTrigger).count() == 1


def test_evaluate_alerts_ignores_inactive(session):
    seed_cities(session)
    sp = city(session)
    session.add(Alert(client_id=uuid.UUID(CLIENT_A), city_id=sp.id, threshold=5, active=False))
    session.flush()
    reading = add_reading(session, sp.id, datetime(2026, 11, 18, 15, 0, tzinfo=UTC), 9)
    assert evaluate_alerts(session, reading, sp) == 0


def test_triggers_listed_for_client(client, session):
    seed_cities(session)
    sp = city(session)
    session.add(Alert(client_id=uuid.UUID(CLIENT_A), city_id=sp.id, threshold=8, active=True))
    session.flush()
    reading = add_reading(session, sp.id, datetime(2026, 11, 18, 16, 0, tzinfo=UTC), 9.5)
    evaluate_alerts(session, reading, sp)
    body = client.get("/api/v1/alerts/triggers", headers=headers(CLIENT_A)).json()
    assert len(body) == 1
    assert body[0]["city_name"] == "São Paulo"
    assert body[0]["uv"] == 9.5
    assert client.get("/api/v1/alerts/triggers", headers=headers(CLIENT_B)).json() == []
