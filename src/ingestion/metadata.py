"""Colunas de metadados adicionadas a toda carga, para rastreabilidade."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

INGESTED_AT_COLUMN = "_ingested_at"
SOURCE_FILE_COLUMN = "_source_file"


def add_ingestion_metadata(
    df: pd.DataFrame,
    source_file: str,
    ingested_at: datetime | None = None,
) -> pd.DataFrame:
    """Retorna uma cópia de `df` com data/hora da ingestão e o arquivo de origem.

    `ingested_at` pode ser injetado para deixar a função determinística nos testes.
    """
    ingested_at = ingested_at or datetime.now(UTC)
    result = df.copy()
    result[INGESTED_AT_COLUMN] = ingested_at
    result[SOURCE_FILE_COLUMN] = source_file
    return result
