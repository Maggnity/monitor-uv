"""Cliente da OpenUV: UV atual por coordenada, autenticado por chave de API."""

import time
from collections.abc import Callable
from datetime import datetime

import httpx

from app.providers.base import CityLike, CurrentReading, ProviderError, get_with_retry

OPENUV_URL = "https://api.openuv.io/api/v1/uv"


def _parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


class OpenUvProvider:
    source = "openuv"

    def __init__(
        self, api_key: str, client: httpx.Client, sleep: Callable[[float], None] = time.sleep
    ):
        self._api_key = api_key
        self._client = client
        self._sleep = sleep

    def fetch_current(self, city: CityLike, now_utc: datetime | None = None) -> CurrentReading:
        response = get_with_retry(
            self._client,
            OPENUV_URL,
            params={"lat": float(city.lat), "lng": float(city.lng)},
            headers={"x-access-token": self._api_key},
            name="OpenUV",
            sleep=self._sleep,
        )
        try:
            result = response.json()["result"]
            uv_max = result.get("uv_max")
            return CurrentReading(
                measured_at=_parse_time(result["uv_time"]),
                uv=float(result["uv"]),
                uv_max=float(uv_max) if uv_max is not None else None,
                uv_max_at=_parse_time(result.get("uv_max_time")),
                source=self.source,
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ProviderError(f"Resposta inesperada da OpenUV: {exc}") from exc
