# Type Hints

> **Purpose**: Annotate Python 3.12+ code so mypy/IDEs catch data-shape bugs before runtime
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

Type hints are optional annotations checked statically by tools like mypy; the
interpreter does not enforce them at runtime. Python 3.12 (PEP 695) added native
generic syntax (`def f[T](...)`, `class Box[T]`) and the `type` statement for
aliases, so `TypeVar` boilerplate is no longer needed. Use built-in generics
(`list[str]`, `dict[str, int]`) and `X | None` unions instead of `typing.List`/`Optional`.

## The Pattern

```python
from collections.abc import Iterable, Iterator, Mapping
from typing import Literal, Protocol, TypedDict, override

type Row = dict[str, str]                 # PEP 695 alias (3.12+)
type Layer = Literal["bronze", "silver", "gold"]

class OrderRecord(TypedDict):
    order_id: int
    amount: float
    customer: str | None

class Sink(Protocol):                     # structural typing ("duck typing")
    def write(self, rows: Iterable[Row]) -> int: ...

def first[T](items: Iterable[T], default: T | None = None) -> T | None:
    return next(iter(items), default)

def parse(rows: Iterable[Row]) -> Iterator[OrderRecord]:
    for r in rows:
        yield {"order_id": int(r["id"]), "amount": float(r["amount"]),
               "customer": r.get("customer") or None}

class Base:
    def name(self) -> str: return "base"

class Child(Base):
    @override                              # 3.12: checker errors if nothing is overridden
    def name(self) -> str: return "child"
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `Optional[int]` | `int \| None` | PEP 604 union syntax (3.10+) |
| `List[str]`, `Dict[str, int]` | `list[str]`, `dict[str, int]` | Built-in generics (3.9+) |
| `T = TypeVar("T")` + `def f(x: T)` | `def f[T](x: T)` | PEP 695 (3.12+) |
| `Alias: TypeAlias = ...` | `type Alias = ...` | Lazily evaluated `TypeAliasType` |
| Parameter accepts any iterable | `Iterable[T]` from `collections.abc` | Accept abstract, return concrete |
| `Mapping[str, Any]` | read-only dict param | Signals no mutation |

## Common Mistakes

### Wrong

```python
from typing import List, Optional, TypeVar
T = TypeVar("T")

def load(paths: List[str], limit: Optional[int] = None) -> List[dict]:
    ...  # bare `dict` loses key/value types; typing.List is deprecated
```

### Correct

```python
from collections.abc import Sequence

def load(paths: Sequence[str], limit: int | None = None) -> list[dict[str, str]]:
    ...
```

## Related

- [dataclasses](../concepts/dataclasses.md)
- [project-setup-uv](../patterns/project-setup-uv.md)
