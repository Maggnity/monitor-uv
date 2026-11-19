import csv
import io
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models import UvDailySummary
from app.seed.cities import seed_cities
from app.seed.history import seed_history
from tests.factories import add_daily, add_hourly

SP = ZoneInfo("America/Sao_Paulo")
TODAY = date(2026, 11, 18)


def sp_hour(hour: int, day: int = 18) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=SP).astimezone(UTC)


def test_history_flags_synthetic(client, session):
    seed_cities(session)
    seed_history(session, TODAY, days_hourly=0, days_daily=30)
    body = client.get("/api/v1/cities/1/history", params={"period": "7d"}).json()
    assert body["contains_synthetic"] is True
    assert len(body["days"]) == 7
    assert body["days"][-1]["date"] == "2026-11-17"
    assert {d["origin"] for d in body["days"]} == {"sintetico"}


def test_history_appends_today_forecast(client, session):
    seed_cities(session)
    seed_history(session, TODAY, days_hourly=0, days_daily=30)
    add_hourly(session, 1, sp_hour(12), 10.4)
    days = client.get("/api/v1/cities/1/history", params={"period": "7d"}).json()["days"]
    assert len(days) == 8
    assert days[-1] == {
        "date": "2026-11-18",
        "uv_max": 10.4,
        "level_key": "very_high",
        "origin": "forecast",
    }


def test_history_invalid_period_422(client, session):
    seed_cities(session)
    assert client.get("/api/v1/cities/1/history", params={"period": "2y"}).status_code == 422


def test_compare_rejects_more_than_4_cities(client, session):
    seed_cities(session)
    response = client.get("/api/v1/compare", params={"city_ids": "1,2,3,4,5"})
    assert response.status_code == 422


def test_compare_trend_up(client, session):
    seed_cities(session)
    for offset in range(1, 8):
        session.add(
            UvDailySummary(
                city_id=1,
                date=TODAY - timedelta(days=offset),
                uv_max=6,
                hours_above_8=0,
                origin="real",
            )
        )
    for hour, uv in [(11, 8.5), (12, 9.0), (13, 8.2)]:
        add_hourly(session, 1, sp_hour(hour), uv)
    body = client.get("/api/v1/compare", params={"city_ids": "1"}).json()
    sp_row = next(r for r in body["rows"] if r["city"]["id"] == 1)
    assert sp_row["trend"] == "up"
    assert sp_row["peak_today"] == 9.0
    assert sp_row["hours_above_8"] == 3
    assert sp_row["sparkline"] == [6, 6, 6, 6, 6, 6, 6, 9.0]
    assert body["contains_synthetic"] is False
    assert [s["city_id"] for s in body["series"]] == [1]
    assert len(body["series"][0]["points"]) == 3


def test_compare_defaults_to_first_four_cities_in_series(client, session):
    seed_cities(session)
    body = client.get("/api/v1/compare").json()
    assert len(body["rows"]) == 5
    assert [s["city_id"] for s in body["series"]] == [1, 2, 3, 4]


def test_export_csv_header_and_rows(client, session):
    seed_cities(session)
    response = client.get("/api/v1/compare/export.csv")
    assert response.headers["content-type"].startswith("text/csv")
    assert "comparativo-uv-2026-11-18.csv" in response.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert rows[0] == [
        "cidade",
        "uf",
        "data",
        "uv_atual",
        "tipo_uv_atual",
        "pico_previsto",
        "horas_acima_de_8",
        "tendencia",
        "vulnerabilidade_estimada_ilustrativa",
    ]
    assert len(rows) == 6


def test_map_tomorrow_uses_daily_forecast(client, session):
    seed_cities(session)
    add_daily(session, 5, date(2026, 11, 19), 13.2)
    body = client.get("/api/v1/map", params={"when": "tomorrow"}).json()
    fortaleza = next(p for p in body if p["city_id"] == 5)
    assert fortaleza["uv"] == 13.2
    assert fortaleza["kind"] == "forecast"
    assert fortaleza["level"]["key"] == "extreme"
    assert len(body) == 5
