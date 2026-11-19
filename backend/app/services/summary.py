"""Resumo diário de UV (implementado na Task 6)."""

from datetime import date

from sqlalchemy.orm import Session

from app.models import City


def refresh_summary(session: Session, city: City, d: date) -> None:
    pass
