import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from app.api.deps import NowDep, SessionDep
from app.api.schemas import AlertCreate, AlertOut, AlertTriggerOut, AlertUpdate, CityOut
from app.models import Alert, City
from app.services import alerts as service
from app.timeutil import local_day_bounds_utc, local_now

router = APIRouter(prefix="/alerts", tags=["Alertas"])

REFERENCE_TZ = "America/Sao_Paulo"


def get_client_id(
    x_client_id: Annotated[
        str | None, Header(description="Identificador anônimo do navegador (UUID)")
    ] = None,
) -> uuid.UUID:
    try:
        return uuid.UUID(x_client_id or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Header X-Client-Id obrigatório") from exc


ClientId = Annotated[uuid.UUID, Depends(get_client_id)]


def _out(alert: Alert, last_triggered_at: datetime | None = None) -> AlertOut:
    return AlertOut(
        id=alert.id,
        city=CityOut.model_validate(alert.city),
        threshold=float(alert.threshold),
        active=alert.active,
        created_at=alert.created_at,
        last_triggered_at=last_triggered_at,
    )


def _own_alert(session, client_id: uuid.UUID, alert_id: int) -> Alert:
    alert = session.get(Alert, alert_id)
    if alert is None or alert.client_id != client_id:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return alert


@router.get("", response_model=list[AlertOut], summary="Alertas deste navegador")
def list_alerts(session: SessionDep, client_id: ClientId):
    return [_out(alert, last) for alert, last in service.list_alerts(session, client_id)]


@router.post("", response_model=AlertOut, status_code=201, summary="Cria um alerta")
def create_alert(body: AlertCreate, session: SessionDep, client_id: ClientId):
    if session.get(City, body.city_id) is None:
        raise HTTPException(status_code=404, detail="Cidade não encontrada")
    alert = Alert(client_id=client_id, city_id=body.city_id, threshold=body.threshold, active=True)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return _out(alert)


@router.patch("/{alert_id}", response_model=AlertOut, summary="Liga/desliga ou muda o limite")
def update_alert(alert_id: int, body: AlertUpdate, session: SessionDep, client_id: ClientId):
    alert = _own_alert(session, client_id, alert_id)
    if body.active is not None:
        alert.active = body.active
    if body.threshold is not None:
        alert.threshold = body.threshold
    session.commit()
    session.refresh(alert)
    return _out(alert)


@router.delete("/{alert_id}", status_code=204, summary="Exclui um alerta")
def delete_alert(alert_id: int, session: SessionDep, client_id: ClientId):
    session.delete(_own_alert(session, client_id, alert_id))
    session.commit()
    return Response(status_code=204)


@router.get("/triggers", response_model=list[AlertTriggerOut], summary="Disparos recentes")
def list_triggers(
    session: SessionDep,
    client_id: ClientId,
    now: NowDep,
    since: datetime | None = Query(None, description="Padrão: início do dia de hoje"),
):
    if since is None:
        since, _ = local_day_bounds_utc(local_now(now, REFERENCE_TZ).date(), REFERENCE_TZ)
    return [
        AlertTriggerOut(
            alert_id=alert.id,
            city_id=alert.city_id,
            city_name=alert.city.name,
            threshold=float(alert.threshold),
            uv=float(reading.uv_index),
            triggered_at=trigger.triggered_at,
        )
        for trigger, alert, reading in service.list_triggers(session, client_id, since)
    ]
