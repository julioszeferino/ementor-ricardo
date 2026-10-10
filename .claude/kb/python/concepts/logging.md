# Logging

> **Purpose**: Emit leveled, configurable diagnostics instead of `print()` in pipelines
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

The stdlib `logging` module routes records from named loggers through handlers and
formatters. Each module creates `logging.getLogger(__name__)`; only the application
entry point configures handlers, preferably with `logging.config.dictConfig()`
(the recommended method for new applications). Pass arguments lazily
(`logger.info("rows=%d", n)`) so filtered messages are never formatted.

## The Pattern

```python
# src/etl/extract.py -- library/module code: never configure handlers here
import logging

logger = logging.getLogger(__name__)          # e.g. "etl.extract"

def extract(table: str) -> int:
    logger.info("extract start table=%s", table)
    try:
        rows = 42
    except OSError:
        logger.exception("extract failed table=%s", table)  # ERROR + traceback
        raise
    logger.debug("extract done table=%s rows=%d", table, rows)
    return rows

# src/etl/__main__.py -- application entry point: configure once
import logging

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    extract("sales")
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `logging.getLogger(__name__)` | Module logger | Hierarchy follows package path |
| `logger.info("n=%d", n)` | Lazy formatting | Preferred over f-strings in log calls |
| `logger.exception("msg")` | ERROR + stack trace | Only inside `except` |
| `logger.warning(..., exc_info=True)` | Any level + traceback | |
| `logging.basicConfig(...)` | Root handler | Scripts; call before first log |
| `dictConfig({... "disable_existing_loggers": False})` | Full config | Default `True` silences existing loggers |
| `getLogger("pkg").addHandler(NullHandler())` | Silent library | Only handler a library should add |

## Common Mistakes

### Wrong

```python
import logging
logging.basicConfig(level=logging.DEBUG)       # configured at import time in a module
logging.info(f"loaded {len(rows)} rows")       # root logger + eager formatting
print("ERROR:", err)                           # no level, no timestamp, no routing
```

### Correct

```python
import logging
logger = logging.getLogger(__name__)
logger.info("loaded rows=%d", len(rows))
logger.error("load failed: %s", err)
```

## Related

- [exceptions](../concepts/exceptions.md)
- [logging-setup](../patterns/logging-setup.md)
