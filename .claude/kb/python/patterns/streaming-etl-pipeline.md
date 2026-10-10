# Streaming ETL Pipeline

> **Purpose**: Extract, validate, transform and load large files in constant memory using composable generators
> **MCP Validated**: 2026-10-09

## When to Use

- Source files are larger than (or close to) available RAM
- Rows must be validated individually, with bad rows quarantined instead of failing the run
- Loading targets prefer bulk inserts of fixed-size batches

## Implementation

```python
"""etl/pipeline.py -- generator-based CSV -> SQLite loader."""
import csv
import logging
import sqlite3
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date
from itertools import batched
from pathlib import Path

logger = logging.getLogger(__name__)

type RawRow = dict[str, str]


@dataclass(frozen=True, slots=True, kw_only=True)
class Sale:
    sale_id: int
    sold_on: date
    amount: float


@dataclass(slots=True)
class RunStats:
    read: int = 0
    loaded: int = 0
    rejected: list[tuple[int, str]] = field(default_factory=list)


def extract(path: Path) -> Iterator[RawRow]:
    with path.open(newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def transform(rows: Iterable[RawRow], stats: RunStats) -> Iterator[Sale]:
    for line_no, raw in enumerate(rows, start=2):        # line 1 is the header
        stats.read += 1
        try:
            sale = Sale(
                sale_id=int(raw["sale_id"]),
                sold_on=date.fromisoformat(raw["sold_on"]),
                amount=float(raw["amount"]),
            )
        except (KeyError, ValueError) as err:
            stats.rejected.append((line_no, repr(err)))
            continue
        yield sale


def load(sales: Iterable[Sale], conn: sqlite3.Connection, stats: RunStats,
         batch_size: int = 1_000) -> None:
    sql = "INSERT OR REPLACE INTO sales (sale_id, sold_on, amount) VALUES (?, ?, ?)"
    for batch in batched(sales, batch_size):
        with conn:                                        # one transaction per batch
            conn.executemany(sql, ((s.sale_id, s.sold_on.isoformat(), s.amount) for s in batch))
        stats.loaded += len(batch)
        logger.debug("batch loaded size=%d total=%d", len(batch), stats.loaded)


def run(src: Path, db: Path, batch_size: int = 1_000) -> RunStats:
    stats = RunStats()
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sales "
            "(sale_id INTEGER PRIMARY KEY, sold_on TEXT, amount REAL)"
        )
        load(transform(extract(src), stats), conn, stats, batch_size)
    finally:
        conn.close()
    logger.info("run done src=%s read=%d loaded=%d rejected=%d",
                src.name, stats.read, stats.loaded, len(stats.rejected))
    return stats
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `batch_size` | `1000` | Rows per `executemany` transaction; tune to target DB |
| `start=2` in `enumerate` | `2` | Aligns reported line numbers with the file (header = 1) |
| `INSERT OR REPLACE` | on | Makes reruns idempotent on primary key |
| `sold_on.isoformat()` | explicit | sqlite3 default date adapter is deprecated since 3.12 |

## Example Usage

```python
import logging
from pathlib import Path
from etl.pipeline import run

logging.basicConfig(level=logging.INFO)
stats = run(Path("data/landing/sales.csv"), Path("data/dw.db"), batch_size=5_000)
if stats.rejected:
    for line_no, reason in stats.rejected[:10]:
        print(f"line {line_no}: {reason}")
```

## See Also

- [error-handling-retry](../patterns/error-handling-retry.md)
- [generators-iterators](../concepts/generators-iterators.md)
