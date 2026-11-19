"""Dependências compartilhadas pelas rotas."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.models import City


def get_now() -> datetime:
    """Relógio da API (sobrescrito nos testes)."""
    return datetime.now(UTC)


SessionDep = Annotated[Session, Depends(get_session)]
NowDep = Annotated[datetime, Depends(get_now)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_city(city_id: int, session: SessionDep) -> City:
    city = session.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="Cidade não encontrada")
    return city


CityDep = Annotated[City, Depends(get_city)]
