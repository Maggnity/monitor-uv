"""Escala do índice UV da OMS: nível, rótulo e recomendação em linguagem simples."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class UvLevel:
    key: str
    label: str
    recommendation: str


LOW = UvLevel("low", "Baixo", "Sem proteção necessária")
MODERATE = UvLevel("moderate", "Moderado", "Use protetor solar e óculos")
HIGH = UvLevel("high", "Alto", "Protetor, chapéu, procure sombra")
VERY_HIGH = UvLevel("very_high", "Muito alto", "Evite sol entre 10h e 16h")
EXTREME = UvLevel("extreme", "Extremo", "Evite exposição; proteção máxima")

LEVELS: tuple[UvLevel, ...] = (LOW, MODERATE, HIGH, VERY_HIGH, EXTREME)


def classify(uv: float) -> UvLevel:
    """Classifica o UV arredondando ao inteiro mais próximo (meio para cima), como a OMS."""
    if uv < 0:
        raise ValueError("O índice UV não pode ser negativo")
    rounded = math.floor(float(uv) + 0.5)
    if rounded <= 2:
        return LOW
    if rounded <= 5:
        return MODERATE
    if rounded <= 7:
        return HIGH
    if rounded <= 10:
        return VERY_HIGH
    return EXTREME
