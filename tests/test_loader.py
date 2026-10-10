from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ingestion.config import DatabaseSettings
from ingestion.loader import get_engine, load_dataframe


def test_load_dataframe_writes_to_raw_schema_by_default() -> None:
    df = MagicMock(spec=pd.DataFrame)
    df.__len__.return_value = 3
    engine = MagicMock()

    rows = load_dataframe(df, "clientes", engine)

    assert rows == 3
    df.to_sql.assert_called_once_with(
        "clientes", engine, schema="raw", if_exists="append", index=False, method="multi"
    )


def test_get_engine_builds_url_from_settings() -> None:
    settings = DatabaseSettings("db", 5432, "warehouse", "user", "secret")

    with patch("ingestion.loader.create_engine") as create_engine:
        get_engine(settings)

    create_engine.assert_called_once_with(settings.url, pool_pre_ping=True)


def test_get_engine_reads_env_when_no_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DW_PASSWORD", "secret")

    with patch("ingestion.loader.create_engine") as create_engine:
        get_engine()

    assert create_engine.call_args.args[0].password == "secret"
