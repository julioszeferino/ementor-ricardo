from datetime import UTC, datetime

import pandas as pd

from ingestion.metadata import INGESTED_AT_COLUMN, SOURCE_FILE_COLUMN, add_ingestion_metadata


def test_adds_metadata_columns_without_mutating_input() -> None:
    df = pd.DataFrame({"id": [1, 2]})
    ingested_at = datetime(2026, 1, 1, tzinfo=UTC)

    result = add_ingestion_metadata(df, "clientes.csv", ingested_at)

    assert list(df.columns) == ["id"]
    assert (result[INGESTED_AT_COLUMN] == ingested_at).all()
    assert (result[SOURCE_FILE_COLUMN] == "clientes.csv").all()


def test_defaults_ingested_at_to_now_in_utc() -> None:
    before = datetime.now(UTC)

    result = add_ingestion_metadata(pd.DataFrame({"id": [1]}), "x.csv")

    assert result[INGESTED_AT_COLUMN].iloc[0] >= before
