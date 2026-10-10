"""DAG de exemplo: ingestão (Python) -> transformação (dbt).

Mantenha a DAG fina: a lógica de negócio fica em `src/ingestion` e no dbt,
onde é testável. Nada de acesso a banco ou leitura de arquivo no topo do módulo.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

DW_PYTHON = "/opt/dw-venv/bin/python"
DBT = "/opt/dw-venv/bin/dbt"

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dw_pipeline",
    description="Ingestão dos arquivos de data/ e build do dbt",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["dw", "exemplo"],
):
    ingest = BashOperator(
        task_id="ingest_raw",
        bash_command=f"{DW_PYTHON} -m ingestion.main",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"{DBT} build --project-dir $DBT_PROJECT_DIR --profiles-dir $DBT_PROFILES_DIR",
    )

    ingest >> dbt_build
