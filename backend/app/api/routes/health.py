from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import SessionDep
from app.api.schemas import HealthOut

router = APIRouter(tags=["Saúde"])


@router.get("/health", response_model=HealthOut, summary="Estado da API e do banco")
def health(session: SessionDep):
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "error"})
    return HealthOut(status="ok", database="ok")
