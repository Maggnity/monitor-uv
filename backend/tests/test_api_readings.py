from datetime import UTC, datetime, timedelta

from app.seed.cities import seed_cities
from tests.factories import add_reading


def test_readings_pagination(client, session):
    seed_cities(session)
    start = datetime(2026, 11, 1, tzinfo=UTC)
    for i in range(120):
        add_reading(session, 1, start + timedelta(hours=i), 3)
    body = client.get("/api/v1/readings", params={"city_id": 1, "page_size": 50, "page": 3}).json()
    assert body["total"] == 120
    assert len(body["items"]) == 20
    assert body["page"] == 3


def test_readings_filters_by_origin_and_orders_desc(client, session):
    seed_cities(session)
    add_reading(session, 1, datetime(2026, 11, 1, 12, tzinfo=UTC), 3, origin="sintetico")
    add_reading(session, 1, datetime(2026, 11, 2, 12, tzinfo=UTC), 4)
    add_reading(session, 1, datetime(2026, 11, 3, 12, tzinfo=UTC), 5)
    items = client.get("/api/v1/readings", params={"origin": "real"}).json()["items"]
    assert [i["uv_index"] for i in items] == [5, 4]


def test_readings_page_size_limit(client, session):
    seed_cities(session)
    assert client.get("/api/v1/readings", params={"page_size": 500}).status_code == 422
