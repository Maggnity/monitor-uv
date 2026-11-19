"""Cliente da OpenUV: UV atual por coordenada, autenticado por chave de API."""

from datetime import datetime

import httpx

from app.providers.base import CityLike, CurrentReading, ProviderError

OPENUV_URL = "https://api.openuv.io/api/v1/uv"


def _parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


class OpenUvProvider:
    source = "openuv"

    def __init__(self, api_key: str, client: httpx.Client):
        self._api_key = api_key
        self._client = client

    def fetch_current(self, city: CityLike, now_utc: datetime | None = None) -> CurrentReading:
        try:
            response = self._client.get(
                OPENUV_URL,
                params={"lat": float(city.lat), "lng": float(city.lng)},
                headers={"x-access-token": self._api_key},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Falha de rede na OpenUV: {exc}") from exc
        if response.status_code != 200:
            raise ProviderError(
                f"OpenUV respondeu {response.status_code}", status=response.status_code
            )
        result = response.json()["result"]
        return CurrentReading(
            measured_at=_parse_time(result["uv_time"]),
            uv=float(result["uv"]),
            uv_max=float(result["uv_max"]) if result.get("uv_max") is not None else None,
            uv_max_at=_parse_time(result.get("uv_max_time")),
            source=self.source,
        )
