from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.api.deps import SessionDep
from app.genetics.service import list_phototypes

router = APIRouter(tags=["Genética"])


class PhototypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str
    med_j_m2: int
    source: str


@router.get(
    "/phototypes",
    response_model=list[PhototypeOut],
    summary="Fototipos de pele (Fitzpatrick) e dose mínima para queimadura",
)
def phototypes(session: SessionDep):
    return list_phototypes(session)
