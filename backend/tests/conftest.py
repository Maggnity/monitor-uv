import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://uv:uv@localhost:5432/uv_test"
)


@pytest.fixture(scope="session")
def engine():
    from app.db import Base

    import app.models  # noqa: F401  (registra os modelos)

    try:
        import app.genetics.models  # noqa: F401
    except ImportError:
        pass

    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    from app.db import Base

    with Session(engine, expire_on_commit=False) as s:
        yield s
        s.rollback()
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    if tables:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
