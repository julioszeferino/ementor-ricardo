"""Escrita de DataFrames no Postgres."""

from __future__ import annotations

import logging
from typing import Literal

import pandas as pd
from sqlalchemy import Engine, create_engine

from ingestion.config import DatabaseSettings

logger = logging.getLogger(__name__)

RAW_SCHEMA = "raw"


def get_engine(settings: DatabaseSettings | None = None) -> Engine:
    settings = settings or DatabaseSettings.from_env()
    return create_engine(settings.url, pool_pre_ping=True)


def load_dataframe(
    df: pd.DataFrame,
    table: str,
    engine: Engine,
    schema: str = RAW_SCHEMA,
    if_exists: Literal["fail", "replace", "append"] = "append",
) -> int:
    """Grava `df` em `schema.table` e retorna o número de linhas escritas.

    Pense na idempotência: rodar a mesma carga duas vezes não deve duplicar dados.
    """
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False, method="multi")
    logger.info("Carregadas %d linhas em %s.%s", len(df), schema, table)
    return len(df)
