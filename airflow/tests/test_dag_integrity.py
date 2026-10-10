"""Testes de integridade das DAGs: todas importam sem erro e têm a estrutura esperada.

Requer Airflow instalado; rode dentro do container (veja README) ou no job `dags` do CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from airflow.dag_processing.dagbag import DagBag

DAGS_DIR = Path(__file__).resolve().parents[1] / "dags"


@pytest.fixture(scope="module")
def dagbag() -> DagBag:
    return DagBag(dag_folder=DAGS_DIR)


def test_no_import_errors(dagbag: DagBag) -> None:
    assert dagbag.import_errors == {}


def test_all_dags_have_tags_and_no_catchup(dagbag: DagBag) -> None:
    assert dagbag.dags, "nenhuma DAG encontrada"
    for dag_id, dag in dagbag.dags.items():
        assert dag.tags, f"{dag_id} sem tags"
        assert dag.catchup is False, f"{dag_id} com catchup ligado"


def test_dw_pipeline_runs_ingestion_before_dbt(dagbag: DagBag) -> None:
    dag = dagbag.dags["dw_pipeline"]

    assert set(dag.task_ids) == {"ingest_raw", "dbt_build"}
    assert dag.get_task("ingest_raw").downstream_task_ids == {"dbt_build"}
