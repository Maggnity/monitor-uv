"""Alertas de UV: disparo quando uma leitura passa do limite (no máximo 1 por dia)."""

import uuid
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models import Alert, AlertTrigger, City, UvReading
from app.timeutil import local_date, local_day_bounds_utc


def evaluate_alerts(session: Session, reading: UvReading, city: City) -> int:
    """Dispara alertas ativos da cidade cujo limite foi ultrapassado (UV > limite)."""
    day = local_date(reading.measured_at, city.timezone)
    start, end = local_day_bounds_utc(day, city.timezone)
    already_today = exists().where(
        AlertTrigger.alert_id == Alert.id,
        AlertTrigger.triggered_at >= start,
        AlertTrigger.triggered_at < end,
    )
    alerts = session.scalars(
        select(Alert).where(
            Alert.city_id == city.id,
            Alert.active.is_(True),
            Alert.threshold < reading.uv_index,
            ~already_today,
        )
    ).all()
    for alert in alerts:
        session.add(
            AlertTrigger(alert_id=alert.id, reading_id=reading.id, triggered_at=reading.measured_at)
        )
    session.flush()
    return len(alerts)


def list_alerts(session: Session, client_id: uuid.UUID) -> list[tuple[Alert, datetime | None]]:
    last = (
        select(AlertTrigger.triggered_at)
        .where(AlertTrigger.alert_id == Alert.id)
        .order_by(AlertTrigger.triggered_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    rows = session.execute(
        select(Alert, last).where(Alert.client_id == client_id).order_by(Alert.created_at, Alert.id)
    )
    return [(alert, last_at) for alert, last_at in rows]


def list_triggers(
    session: Session, client_id: uuid.UUID, since: datetime
) -> list[tuple[AlertTrigger, Alert, UvReading]]:
    rows = session.execute(
        select(AlertTrigger, Alert, UvReading)
        .join(Alert, Alert.id == AlertTrigger.alert_id)
        .join(UvReading, UvReading.id == AlertTrigger.reading_id)
        .where(Alert.client_id == client_id, AlertTrigger.triggered_at >= since)
        .order_by(AlertTrigger.triggered_at.desc())
    )
    return [tuple(row) for row in rows]
