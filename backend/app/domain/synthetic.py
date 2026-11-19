"""Curva sintética de UV: sino diário com pico perto do meio-dia e sazonalidade por latitude.

Usada pelo provedor simulado e pelo histórico de demonstração. Todo dado gerado aqui é
gravado como `sintetico`.
"""

import math
import random
from datetime import date

PEAK_BASE: dict[str, float] = {
    "SP-01": 10,
    "RJ-01": 11,
    "BH-01": 11,
    "CWB-01": 9,
    "FOR-01": 13,
}

PEAK_HOUR = 12.25
SPREAD_HOURS = 2.3
NOISE = 0.03


def bell_uv(local_hour: float, peak: float) -> float:
    if not 6 <= local_hour <= 19:
        return 0.0
    value = peak * math.exp(-((local_hour - PEAK_HOUR) ** 2) / (2 * SPREAD_HOURS**2))
    return round(max(value, 0.0), 2)


def _seasonal_amplitude(lat: float) -> float:
    if abs(lat) < 10:
        return 0.08
    if abs(lat) > 24:
        return 0.35
    return 0.25


def seasonal_peak(peak_base: float, lat: float, d: date, rng: random.Random) -> float:
    """Pico do dia: máximo no solstício de verão do hemisfério sul (~21/12)."""
    day_of_year = d.timetuple().tm_yday
    factor = 1 + _seasonal_amplitude(float(lat)) * math.cos(2 * math.pi * (day_of_year - 355) / 365)
    noise = rng.uniform(1 - NOISE, 1 + NOISE)
    return round(max(peak_base * factor * noise, 0.0), 2)


def day_rng(station_code: str, d: date) -> random.Random:
    """Gerador determinístico por estação e dia: o mesmo dia gera sempre a mesma curva."""
    return random.Random(f"{station_code}:{d.isoformat()}")
