"""Processo do coletor: roda as coletas na subida e depois de tempos em tempos.

Uso: python -m app.collector.main
"""

import logging
from datetime import UTC, datetime

import httpx
from apscheduler.schedulers.blocking import BlockingScheduler

from app.collector.jobs import collect_current, collect_forecast
from app.config import Settings, get_settings
from app.db import SessionLocal
from app.providers.base import CurrentProvider, ForecastProvider
from app.providers.openmeteo import OpenMeteoProvider
from app.providers.openuv import OpenUvProvider
from app.providers.simulated import SimulatedProvider

logger = logging.getLogger("collector")


def build_providers(settings: Settings) -> tuple[CurrentProvider, ForecastProvider]:
    if settings.effective_provider == "simulado":
        if settings.uv_provider == "openuv":
            logger.warning("OPENUV_API_KEY vazia — usando provedor simulado")
        simulated = SimulatedProvider()
        return simulated, simulated
    client = httpx.Client()
    return OpenUvProvider(settings.openuv_api_key, client), OpenMeteoProvider(client)


def run_current(provider: CurrentProvider, settings: Settings) -> None:
    try:
        with SessionLocal() as session:
            saved = collect_current(session, provider, datetime.now(UTC), settings)
        logger.info("Coleta de UV atual: %d leitura(s) gravada(s)", saved)
    except Exception:
        logger.exception("Erro inesperado na coleta de UV atual")


def run_forecast(provider: ForecastProvider) -> None:
    try:
        with SessionLocal() as session:
            updated = collect_forecast(session, provider, datetime.now(UTC))
        logger.info("Coleta de previsão: %d cidade(s) atualizada(s)", updated)
    except Exception:
        logger.exception("Erro inesperado na coleta de previsão")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    current, forecast = build_providers(settings)
    logger.info(
        "Coletor iniciado: provedor=%s, UV atual a cada %d min (janela %dh–%dh), "
        "previsão a cada %d min",
        settings.effective_provider,
        settings.openuv_interval_min,
        settings.collect_window_start_hour,
        settings.collect_window_end_hour,
        settings.openmeteo_interval_min,
    )
    run_forecast(forecast)
    run_current(current, settings)

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_current, "interval", minutes=settings.openuv_interval_min, args=[current, settings]
    )
    scheduler.add_job(
        run_forecast, "interval", minutes=settings.openmeteo_interval_min, args=[forecast]
    )
    scheduler.start()


if __name__ == "__main__":
    main()
