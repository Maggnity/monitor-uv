"""Prepara o banco: migrations, cidades e histórico sintético. Idempotente.

Uso: python -m app.seed.main
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.db import SessionLocal
from app.seed.cities import seed_cities
from app.seed.history import seed_history
from app.timeutil import local_date

logger = logging.getLogger("seed")
BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(config, "head")


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def main() -> None:
    run_migrations()
    # O Alembic reconfigura o logging; restaura o nível INFO para as mensagens do seed.
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, force=True)
    with SessionLocal() as session:
        cities = seed_cities(session)
        today = local_date(datetime.now(UTC), "America/Sao_Paulo")
        days = seed_history(session, today)
        try:
            from app.genetics.seed import seed_genetics
        except ImportError:
            pass
        else:
            seed_genetics(session)
    logger.info("Seed concluído: %d cidades, %d dia(s) sintético(s) criados", cities, days)


if __name__ == "__main__":
    main()
