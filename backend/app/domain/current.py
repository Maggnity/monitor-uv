"""Qual valor mostrar como "UV agora" e em que estado a cidade está.

Regras (spec, seção 5.0):
1. Sem leitura e sem estimativa: `no_data`.
2. Mostra a medição se tiver menos de 30 min; senão a estimativa da previsão, rotulada.
3. `night` quando o valor mostrado é ~0 fora do período de sol (tem precedência).
4. `stale` só dentro da janela de coleta (a partir da 1ª coleta esperada do dia), quando a medição tem mais de 2x o intervalo;
   nesse caso mostra o último valor medido, marcado como desatualizado.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from app.domain.uv_scale import UvLevel, classify
from app.timeutil import local_now

FRESH = timedelta(minutes=30)
DAYLIGHT_HOURS = range(6, 18)

Status = Literal["ok", "stale", "night", "no_data"]
Kind = Literal["measured", "estimated"]


@dataclass(frozen=True)
class CurrentState:
    status: Status
    display_uv: float | None
    display_kind: Kind | None
    measured_uv: float | None
    measured_at: datetime | None
    estimated_uv: float | None
    level: UvLevel | None


def resolve_current(
    now_utc: datetime,
    tz: str,
    last_reading: tuple[datetime, float] | None,
    estimated_now: float | None,
    interval_min: int,
    window: tuple[int, int],
) -> CurrentState:
    measured_at, measured_uv = last_reading if last_reading else (None, None)
    if measured_uv is None and estimated_now is None:
        return CurrentState("no_data", None, None, None, None, None, None)

    age = now_utc - measured_at if measured_at else None
    if measured_uv is not None and (age < FRESH or estimated_now is None):
        display, kind = measured_uv, "measured"
    else:
        display, kind = estimated_now, "estimated"

    local = local_now(now_utc, tz)
    status: Status = "ok"
    if display < 0.5 and local.hour not in DAYLIGHT_HOURS:
        status = "night"
    elif measured_uv is not None and _inside_window(local, window, interval_min):
        if age > timedelta(minutes=2 * interval_min):
            status = "stale"
            display, kind = measured_uv, "measured"

    return CurrentState(
        status=status,
        display_uv=display,
        display_kind=kind,
        measured_uv=measured_uv,
        measured_at=measured_at,
        estimated_uv=estimated_now,
        level=classify(display),
    )


def _inside_window(local: datetime, window: tuple[int, int], interval_min: int) -> bool:
    """A partir da 1ª coleta esperada do dia até um intervalo depois da última."""
    start, end = window
    hours = local.hour + local.minute / 60
    tolerance = interval_min / 60
    return start + tolerance <= hours <= end + tolerance
