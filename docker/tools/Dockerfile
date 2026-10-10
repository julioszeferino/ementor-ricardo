# Imagem com o pacote de ingestão e o dbt. Usada pelos serviços `ingestion` e `dbt`.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src

RUN pip install --no-cache-dir uv==0.13.0

WORKDIR /app
# Só os manifests: o código em src/ e dbt/ é montado via volume no compose.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --group dbt --no-install-project

RUN useradd --create-home --uid 1000 app
USER app
