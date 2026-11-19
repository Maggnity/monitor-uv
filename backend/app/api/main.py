"""Aplicação FastAPI do Monitor UV. Swagger em /docs."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, cities, city_map, compare, health, readings
from app.config import get_settings

API_PREFIX = "/api/v1"

DESCRIPTION = """
API de consulta do **Monitor UV**: índice ultravioleta por cidade, coletado da
[OpenUV](https://www.openuv.io) (chave de API) e da [Open-Meteo](https://open-meteo.com)
(previsão), e armazenado em PostgreSQL.

* O nível de risco segue a escala da OMS e vem pronto em `level`.
* `display_kind` diz se o valor é **medido** ou **estimado** pela previsão.
* Respostas de histórico avisam quando o período contém dados **sintéticos** de demonstração.
"""

app = FastAPI(title="Monitor UV API", version="1.0.0", description=DESCRIPTION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (health, cities, compare, city_map, readings, alerts):
    app.include_router(module.router, prefix=API_PREFIX)
