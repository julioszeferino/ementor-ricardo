# Dataclasses

> **Purpose**: Define typed, low-boilerplate record and config objects with the stdlib
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

`@dataclass` generates `__init__`, `__repr__` and `__eq__` from annotated class
fields. For data engineering, prefer `frozen=True` (immutable, hashable),
`slots=True` (3.10+, less memory per instance) and `kw_only=True` (3.10+, explicit
call sites) for records and configs. Use `field(default_factory=...)` for mutable
defaults and `__post_init__` for validation or derived fields.

## The Pattern

```python
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from decimal import Decimal

@dataclass(frozen=True, slots=True, kw_only=True)
class Sale:
    sale_id: int
    sold_on: date
    amount: Decimal
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"amount must be >= 0, got {self.amount}")

@dataclass(slots=True, kw_only=True)
class LoadStats:
    table: str
    rows: int = 0
    errors: list[str] = field(default_factory=list)   # never `= []`

sale = Sale(sale_id=1, sold_on=date(2026, 1, 31), amount=Decimal("9.90"))
fixed = replace(sale, amount=Decimal("10.00"))         # new object; __post_init__ re-runs
print(asdict(fixed))  # {'sale_id': 1, 'sold_on': ..., 'amount': Decimal('10.00'), 'tags': ()}
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `@dataclass(frozen=True)` | Assignment raises `FrozenInstanceError` | Also makes instances hashable |
| `@dataclass(slots=True)` | Generates `__slots__` | 3.10+; no dynamic attributes |
| `@dataclass(kw_only=True)` | Keyword-only `__init__` | 3.10+; avoids positional mixups |
| `x: list = []` | `ValueError` at class creation | Use `field(default_factory=list)` |
| `replace(obj, **changes)` | New instance | Calls `__init__` -> `__post_init__` |
| `asdict(obj)` | Recursive `dict` | Deep-copies non-dataclass values |

## Common Mistakes

### Wrong

```python
@dataclass
class Batch:
    rows = []            # no annotation -> not a field; shared class attribute
    size: int = "100"    # type hints are not enforced at runtime
```

### Correct

```python
@dataclass(kw_only=True)
class Batch:
    rows: list[dict[str, str]] = field(default_factory=list)
    size: int = 100
    # Need runtime validation/coercion of external input? Use pydantic instead.
```

## Related

- [type-hints](../concepts/type-hints.md)
- [streaming-etl-pipeline](../patterns/streaming-etl-pipeline.md)
