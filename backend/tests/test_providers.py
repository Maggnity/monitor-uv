from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
import respx

from app.providers.base import ProviderError
from app.providers.openmeteo import OpenMeteoProvider
from app.providers.openuv import OpenUvProvider

SAO_PAULO = SimpleNamespace(
    id=1, lat=-23.5505, lng=-46.6333, timezone="America/Sao_Paulo", station_code="SP-01"
)

OPENUV_BODY = {
    "result": {
        "uv": 3.2,
        "uv_time": "2026-11-18T13:00:00.000Z",
        "uv_max": 10.1,
        "uv_max_time": "2026-11-18T15:10:00.000Z",
    }
}


@respx.mock
def test_openuv_sends_key_header_and_dynamic_coords():
    route = respx.get("https://api.openuv.io/api/v1/uv").mock(
        return_value=httpx.Response(200, json=OPENUV_BODY)
    )
    reading = OpenUvProvider("k", httpx.Client()).fetch_current(SAO_PAULO)

    request = route.calls.last.request
    assert request.headers["x-access-token"] == "k"
    assert request.url.params["lat"] == "-23.5505"
    assert request.url.params["lng"] == "-46.6333"
    assert reading.uv == 3.2
    assert reading.uv_max == 10.1
    assert reading.measured_at == datetime(2026, 11, 18, 13, 0, tzinfo=UTC)
    assert reading.uv_max_at == datetime(2026, 11, 18, 15, 10, tzinfo=UTC)
    assert reading.source == "openuv"


@pytest.mark.parametrize("status", [401, 429])
@respx.mock
def test_openuv_raises_provider_error_on_http_error(status):
    respx.get("https://api.openuv.io/api/v1/uv").mock(return_value=httpx.Response(status))
    with pytest.raises(ProviderError) as exc:
        OpenUvProvider("k", httpx.Client()).fetch_current(SAO_PAULO)
    assert exc.value.status == status


@respx.mock
def test_openmeteo_parses_hourly_and_daily_to_utc():
    route = respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(
            200,
            json={
                "hourly": {"time": ["2026-11-18T12:00"], "uv_index": [9.5]},
                "daily": {
                    "time": ["2026-11-18"],
                    "uv_index_max": [11.2],
                    "weather_code": [3],
                },
            },
        )
    )
    forecast = OpenMeteoProvider(httpx.Client()).fetch_forecast(SAO_PAULO)

    params = route.calls.last.request.url.params
    assert params["latitude"] == "-23.5505"
    assert params["timezone"] == "America/Sao_Paulo"
    assert forecast.hourly[0].forecast_for == datetime(2026, 11, 18, 15, 0, tzinfo=UTC)
    assert forecast.hourly[0].uv == 9.5
    assert forecast.daily[0].uv_max == 11.2
    assert forecast.daily[0].weather_code == 3
    assert forecast.source == "openmeteo"
