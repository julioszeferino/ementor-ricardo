# Testing Data Code with pytest

> **Purpose**: Test transforms and I/O deterministically using fixtures, parametrization and temporary files
> **MCP Validated**: 2026-10-09

## When to Use

- Unit-testing pure transform functions with many edge-case inputs
- Testing file/DB loaders without touching real data (`tmp_path`, in-memory SQLite)
- Sharing expensive setup (sample datasets, DB schema) across many tests

## Implementation

```python
# tests/conftest.py -- fixtures here are visible to every test without import
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def sales_csv(tmp_path: Path) -> Path:            # tmp_path: unique dir per test
    path = tmp_path / "sales.csv"
    path.write_text(
        "sale_id,sold_on,amount\n"
        "1,2026-01-31,9.90\n"
        "2,not-a-date,5.00\n"
        "3,2026-02-01,12.50\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Path]:
    path = tmp_path / "dw.db"
    yield path                                    # code after yield = teardown
    path.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def reference_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("reference")   # built once per session
```

```python
# tests/unit/test_pipeline.py
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from etl.pipeline import RunStats, Sale, run, transform


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"sale_id": "1", "sold_on": "2026-01-31", "amount": "9.9"},
         Sale(sale_id=1, sold_on=date(2026, 1, 31), amount=9.9)),
        ({"sale_id": "2", "sold_on": "2026-02-01", "amount": "0"},
         Sale(sale_id=2, sold_on=date(2026, 2, 1), amount=0.0)),
    ],
    ids=["regular", "zero-amount"],
)
def test_transform_valid(raw: dict[str, str], expected: Sale) -> None:
    assert list(transform([raw], RunStats())) == [expected]


@pytest.mark.parametrize("bad", [{"sale_id": "x"}, {}, {"sale_id": "1", "sold_on": "?"}])
def test_transform_rejects(bad: dict[str, str]) -> None:
    stats = RunStats()
    assert list(transform([bad], stats)) == []
    assert len(stats.rejected) == 1


def test_run_end_to_end(sales_csv: Path, db: Path) -> None:
    stats = run(sales_csv, db, batch_size=1)
    assert (stats.read, stats.loaded, len(stats.rejected)) == (3, 2, 1)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT SUM(amount) FROM sales").fetchone()[0] == pytest.approx(22.4)


def test_sale_rejects_bad_date() -> None:
    with pytest.raises(ValueError, match=r"month must be in 1\.\.12"):
        date.fromisoformat("2026-13-01")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `@pytest.fixture(scope=...)` | `"function"` | Also `class`, `module`, `package`, `session` |
| `tool.pytest.ini_options.testpaths` | rootdir | Where pytest collects tests |
| `--strict-markers` | off | Error on unregistered `@pytest.mark.*` |
| `--import-mode=importlib` | `prepend` | Recommended for new projects; no `sys.path` hacks |
| `pytest.approx(x)` | rel `1e-6` | Float comparison tolerance |

## Example Usage

```bash
uv run pytest                          # all tests
uv run pytest tests/unit -k transform  # filter by name expression
uv run pytest -x --lf                  # stop at first failure, rerun last failed
uv run pytest --cov=src --cov-report=term-missing
```

## See Also

- [streaming-etl-pipeline](../patterns/streaming-etl-pipeline.md)
- [pathlib-file-io](../concepts/pathlib-file-io.md)
