"""Avaliação de alertas (implementada na Task 10)."""

from sqlalchemy.orm import Session

from app.models import City, UvReading


def evaluate_alerts(session: Session, reading: UvReading, city: City) -> int:
    return 0
