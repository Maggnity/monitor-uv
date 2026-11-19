FROM python:3.12.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências com versões travadas (requirements.lock) em camada própria, para cache.
COPY requirements.lock ./
RUN pip install -r requirements.lock

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-deps .

COPY alembic.ini ./
COPY migrations ./migrations

RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
