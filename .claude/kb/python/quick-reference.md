# Python Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-10-09

## Modern Syntax (3.10 - 3.12+)

| Old | Modern | Since |
|-----|--------|-------|
| `Optional[int]`, `Union[a, b]` | `int \| None`, `a \| b` | 3.10 |
| `List[str]`, `Dict[str, int]` | `list[str]`, `dict[str, int]` | 3.9 |
| `T = TypeVar("T")` | `def f[T](x: T) -> T` | 3.12 |
| `X: TypeAlias = ...` | `type X = ...` | 3.12 |
| manual chunking loop | `itertools.batched(it, n)` | 3.12 |
| `raise X() from e` + message hacks | `exc.add_note("ctx")` | 3.11 |
| `os.path.join(a, b)` | `Path(a) / b` | 3.4 |

## uv / Tooling Commands

| Task | Command |
|------|---------|
| New project (src layout) | `uv init --package dw` |
| Add runtime / dev dependency | `uv add polars` / `uv add --dev pytest` |
| Install exactly from lockfile (CI) | `uv sync --locked` |
| Production install | `uv sync --no-dev` |
| Run in venv | `uv run pytest`, `uv run python -m dw` |
| Lint + autofix / format | `uv run ruff check --fix .` / `uv run ruff format .` |
| Type check | `uv run mypy src` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Internal typed record / config | `@dataclass(frozen=True, slots=True, kw_only=True)` |
| Validate/coerce untrusted external input | pydantic model |
| File larger than RAM | Generator chain + `batched` |
| Resource needing cleanup | `with` + `@contextmanager` (`try/finally`) |
| Dynamic number of resources | `contextlib.ExitStack` |
| Retry network calls | Retry decorator on `TransientError` only |
| Report many validation errors at once | `ExceptionGroup` + `except*` |
| Log setup in an application | `logging.config.dictConfig` at entry point |
| Temp files in tests | `tmp_path` (function) / `tmp_path_factory` (session) |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `def f(x=[])` / `x: list = []` in dataclass | `None` default / `field(default_factory=list)` |
| `except:` or `except Exception: pass` | Catch specific types; log and re-raise |
| `logger.info(f"rows={n}")` | `logger.info("rows=%d", n)` |
| `logging.basicConfig()` inside a library module | Configure only in `main()` |
| Iterate a generator twice | Single pass, or materialize with `list()` deliberately |
| `open(p)` without `encoding` | `p.open(encoding="utf-8")`, `newline=""` for csv |
| Write output in place | Write `.tmp` then `Path.replace()` |
| `pip install` globally | `uv add` + commit `uv.lock` |
| `@contextmanager` without `try/finally` | Wrap `yield` in `try/finally` |

## Related Documentation

| Topic | Path |
|-------|------|
| Getting Started | `concepts/packaging-venv.md` |
| Project bootstrap | `patterns/project-setup-uv.md` |
| Toolchain spec | `specs/python-toolchain.yaml` |
| Full Index | `index.md` |
