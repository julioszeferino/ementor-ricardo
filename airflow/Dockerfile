# Airflow oficial + venv isolado com ingestão e dbt (evita conflito com as libs do Airflow).
FROM apache/airflow:3.3.2-python3.12

USER root
COPY pyproject.toml uv.lock /opt/project/
RUN python -m venv /opt/dw-venv \
 && /opt/dw-venv/bin/pip install --no-cache-dir uv==0.13.0 \
 && cd /opt/project \
 && UV_PROJECT_ENVIRONMENT=/opt/dw-venv /opt/dw-venv/bin/uv sync --locked --no-dev --group dbt --no-install-project \
 && chown -R airflow:0 /opt/project
USER airflow

# pytest no ambiente do Airflow para os testes de integridade das DAGs (airflow/tests).
RUN pip install --no-cache-dir pytest==9.1.1
