"""Tempo estimado até a queimadura (eritema) para um fototipo, dado o índice UV.

1 unidade de índice UV = 0,025 W/m² de irradiância eritêmica. A pele atinge a dose
eritematosa mínima (MED, em J/m²) após MED / irradiância segundos.
"""

UV_INDEX_TO_W_M2 = 0.025
MIN_UV = 0.5
SENSITIVE_PHOTOTYPES = ("I", "II", "III")


def minutes_to_burn(uv: float, med_j_m2: float) -> int | None:
    if uv < MIN_UV:
        return None
    return round(med_j_m2 / (uv * UV_INDEX_TO_W_M2) / 60)


def vulnerability(peak_uv: float | None, sensitive_share: float | None) -> float | None:
    """Índice ilustrativo: pico de UV × proporção da população com fototipos I–III."""
    if peak_uv is None or sensitive_share is None:
        return None
    return round(peak_uv * sensitive_share, 1)
