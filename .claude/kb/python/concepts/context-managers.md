# Context Managers

> **Purpose**: Guarantee setup/teardown of resources (files, connections, transactions, timers)
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A context manager wraps a block with `__enter__`/`__exit__`, so cleanup runs even
when an exception is raised. Use `with` for anything that must be closed or
committed. `contextlib.contextmanager` turns a generator into a context manager,
and `ExitStack` manages a dynamic number of resources.

## The Pattern

```python
import logging
import sqlite3
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

@contextmanager
def transaction(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise                      # never swallow: re-raise after cleanup
    finally:
        conn.close()

@contextmanager
def timed(step: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("step=%s elapsed=%.2fs", step, time.perf_counter() - start)

with timed("load"), transaction(Path("dw.db")) as conn:
    conn.execute("INSERT INTO sales VALUES (?, ?)", (1, 9.9))

with ExitStack() as stack:          # open N files, all closed on exit
    files = [stack.enter_context(p.open()) for p in Path("in").glob("*.csv")]
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `with open(p) as f:` | File closed on exit | Even on exception |
| `@contextmanager` + `yield` | Generator-based CM | Wrap `yield` in `try/finally` |
| `ExitStack().enter_context(cm)` | Dynamic set of CMs | Unwinds in reverse order |
| `contextlib.suppress(FileNotFoundError)` | Ignore one exception type | Be specific |
| `with sqlite3.connect(db) as c:` | Commits/rolls back only | Does NOT close the connection |
| `with a(), b():` | Nested CMs, one line | Parenthesized form allowed (3.10+) |

## Common Mistakes

### Wrong

```python
@contextmanager
def connect(url: str):
    conn = make_conn(url)
    yield conn
    conn.close()          # skipped if the body raises -> connection leak
```

### Correct

```python
@contextmanager
def connect(url: str) -> Iterator[Conn]:
    conn = make_conn(url)
    try:
        yield conn
    finally:
        conn.close()
```

## Related

- [pathlib-file-io](../concepts/pathlib-file-io.md)
- [error-handling-retry](../patterns/error-handling-retry.md)
