# Exceptions

> **Purpose**: Raise, catch and chain errors so pipeline failures are explicit and debuggable
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

Python signals errors with exceptions; catch only what you can handle and let the
rest propagate. Define a small project exception hierarchy so callers can catch
your errors by category, chain with `raise ... from err` to keep the root cause,
and use `add_note()` (3.11+) to attach context such as file or row number.
`ExceptionGroup` with `except*` (3.11+) reports several independent failures at once.

## The Pattern

```python
class PipelineError(Exception):
    """Base class for all project errors."""

class ExtractError(PipelineError): ...
class ValidationError(PipelineError): ...
class TransientError(PipelineError):
    """Safe to retry (timeouts, throttling)."""

def parse_amount(raw: str, *, line: int) -> float:
    try:
        return float(raw)
    except ValueError as err:
        exc = ValidationError(f"invalid amount {raw!r}")
        exc.add_note(f"line={line}")              # 3.11+: shown in traceback
        raise exc from err                        # preserves original cause

def validate_all(rows: list[dict[str, str]]) -> None:
    errors: list[Exception] = []
    for i, row in enumerate(rows, start=2):
        try:
            parse_amount(row["amount"], line=i)
        except ValidationError as e:
            errors.append(e)
    if errors:
        raise ExceptionGroup("validation failed", errors)

try:
    validate_all([{"amount": "x"}, {"amount": "1.5"}])
except* ValidationError as eg:                    # handles the matching subgroup
    print(f"{len(eg.exceptions)} bad rows")
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `raise New(...) from err` | Sets `__cause__` | "The above exception was the direct cause" |
| `raise New(...) from None` | Hides original context | Use sparingly |
| `exc.add_note("ctx")` | Extra traceback line | 3.11+ |
| `except* TypeA:` | Matches inside `ExceptionGroup` | 3.11+ |
| `try/except/else/finally` | `else` runs only if no exception | Keep `try` body minimal |
| `except Exception:` | Catches almost all | Not `KeyboardInterrupt`/`SystemExit` |

## Common Mistakes

### Wrong

```python
try:
    load(batch)
except:                  # bare except: also catches Ctrl+C and SystemExit
    pass                 # silently loses data
```

### Correct

```python
try:
    load(batch)
except TransientError:
    logger.warning("transient failure, will retry", exc_info=True)
    raise
```

## Related

- [logging](../concepts/logging.md)
- [error-handling-retry](../patterns/error-handling-retry.md)
