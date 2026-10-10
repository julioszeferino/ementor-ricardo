# pathlib and File I/O

> **Purpose**: Manipulate paths and read/write files portably and safely
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

`pathlib.Path` is the object-oriented replacement for `os.path` string handling:
paths join with `/`, expose `.suffix`, `.stem`, `.parent`, and offer `glob`/`rglob`
for discovering partitions. Always pass `encoding="utf-8"` for text files (the
platform default may differ) and `newline=""` when using the `csv` module. Write to
a temporary file and `replace()` it into place so readers never see partial output.

## The Pattern

```python
import csv
import json
import os
from collections.abc import Iterable
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"   # anchored, not cwd-relative

def partition_path(base: Path, table: str, dt: str) -> Path:
    p = base / "bronze" / table / f"dt={dt}"
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_csv_atomic(path: Path, rows: Iterable[dict[str, str]], fields: list[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)                     # atomic rename on the same filesystem

def load_config(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))

for csv_file in sorted((DATA_DIR / "landing").glob("*.csv")):
    print(csv_file.stem, csv_file.stat().st_size)
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `Path("a") / "b" / "c.csv"` | `a/b/c.csv` | OS-correct separators |
| `p.suffix`, `p.stem`, `p.name` | `.csv`, `c`, `c.csv` | |
| `p.with_suffix(".parquet")` | Same path, new extension | |
| `p.glob("*.csv")` / `p.rglob("*.csv")` | Iterator of paths | `rglob` is recursive |
| `p.mkdir(parents=True, exist_ok=True)` | Idempotent mkdir | |
| `p.read_text(encoding="utf-8")` | `str` | Small files only; stream big ones |
| `p.unlink(missing_ok=True)` | Delete if present | 3.8+ |

## Common Mistakes

### Wrong

```python
import os
path = os.path.join("data", "out") + "/" + name + ".csv"   # manual separators
f = open(path, "w")                                          # no encoding, never closed
f.write(content)                                             # readers may see partial file
```

### Correct

```python
path = Path("data") / "out" / f"{name}.csv"
write_csv_atomic(path, rows, fields)
```

## Related

- [context-managers](../concepts/context-managers.md)
- [streaming-etl-pipeline](../patterns/streaming-etl-pipeline.md)
