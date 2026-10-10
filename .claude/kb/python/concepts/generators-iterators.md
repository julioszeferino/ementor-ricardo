# Generators and Iterators

> **Purpose**: Process datasets lazily, one record or batch at a time, in constant memory
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

An iterator produces values on demand via `__next__`; a generator function (any
function containing `yield`) is the simplest way to build one. Chaining generators
creates a streaming pipeline where only the current record lives in memory, which
lets you process files larger than RAM. `itertools.batched` (3.12+) groups a stream
into fixed-size tuples for bulk inserts.

## The Pattern

```python
import csv
from collections.abc import Iterable, Iterator
from itertools import batched, islice
from pathlib import Path

def read_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:   # closed when generator finishes
        yield from csv.DictReader(f)

def only_valid(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        if row.get("amount"):
            yield row

def to_amounts(rows: Iterable[dict[str, str]]) -> Iterator[float]:
    return (float(r["amount"]) for r in rows)           # generator expression

rows = only_valid(read_rows(Path("sales.csv")))         # nothing read yet (lazy)
for batch in batched(rows, 1_000):                      # tuple of <= 1000 rows
    ...                                                 # bulk insert batch
preview = list(islice(read_rows(Path("sales.csv")), 5)) # first 5 rows only
total = sum(to_amounts(only_valid(read_rows(Path("sales.csv")))))
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `batched("ABCDEFG", 3)` | `('A','B','C') ('D','E','F') ('G',)` | 3.12+; last batch may be shorter |
| `islice(it, 5)` | First 5 items | Like `head`; does not load the rest |
| `yield from other` | Delegates to sub-iterator | Flattens nested generators |
| `chain.from_iterable(files)` | One stream from many | Concatenate partitions |
| `[x for x in rows]` | `list` (eager) | Use `(x for x in rows)` for lazy |
| `Iterator[T]` | Return type of a generator | `Generator[Y, S, R]` only if using send/return |

## Common Mistakes

### Wrong

```python
rows = read_rows(Path("sales.csv"))
count = sum(1 for _ in rows)
total = sum(float(r["amount"]) for r in rows)   # 0 -- generator already exhausted

def read_all(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open()))    # loads full file; leaks file handle
```

### Correct

```python
count = total = 0
for r in read_rows(Path("sales.csv")):          # single pass, constant memory
    count += 1
    total += float(r["amount"])
```

## Related

- [context-managers](../concepts/context-managers.md)
- [streaming-etl-pipeline](../patterns/streaming-etl-pipeline.md)
