from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion import main as main_module
from ingestion.main import main, run


def test_run_sums_rows_of_all_pipelines() -> None:
    engine = MagicMock()
    first = MagicMock(return_value=2)
    second = MagicMock(return_value=5)

    total = run(Path("data"), engine, {"a": first, "b": second})

    assert total == 7
    first.assert_called_once_with(Path("data"), engine)


def test_run_with_no_pipelines_returns_zero() -> None:
    assert run(Path("data"), MagicMock(), {}) == 0


def test_main_uses_registered_pipelines(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = MagicMock(return_value=1)
    monkeypatch.setitem(main_module.PIPELINES, "fake", pipeline)
    monkeypatch.setenv("DATA_DIR", "/tmp/data")  # noqa: S108

    with patch("ingestion.main.get_engine"):
        assert main() == 0

    assert pipeline.call_args.args[0] == Path("/tmp/data")  # noqa: S108
