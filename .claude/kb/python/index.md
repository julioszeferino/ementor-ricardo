# Python Knowledge Base

> **Purpose**: Modern Python (3.12+) for data engineering -- typing, records, streaming, I/O, errors, logging, packaging with uv, testing and code quality
> **MCP Validated**: 2026-10-09

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/type-hints.md](concepts/type-hints.md) | Built-in generics, `X \| None`, PEP 695 generics/`type`, Protocol, `@override` |
| [concepts/dataclasses.md](concepts/dataclasses.md) | Typed records/configs with `frozen`, `slots`, `kw_only`, `default_factory` |
| [concepts/generators-iterators.md](concepts/generators-iterators.md) | Lazy, constant-memory streaming; `yield from`, `islice`, `batched` |
| [concepts/context-managers.md](concepts/context-managers.md) | Guaranteed cleanup; `@contextmanager`, `ExitStack`, transactions |
| [concepts/exceptions.md](concepts/exceptions.md) | Exception hierarchies, chaining, `add_note`, `ExceptionGroup`/`except*` |
| [concepts/logging.md](concepts/logging.md) | Module loggers, lazy formatting, `logger.exception`, library rules |
| [concepts/pathlib-file-io.md](concepts/pathlib-file-io.md) | `Path` operations, encodings, CSV/JSON I/O, atomic writes |
| [concepts/packaging-venv.md](concepts/packaging-venv.md) | `.venv`, `pyproject.toml`, dependency groups, `uv.lock`, src layout |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/project-setup-uv.md](patterns/project-setup-uv.md) | Bootstrap project with uv + ruff + mypy + pytest + CI gates |
| [patterns/streaming-etl-pipeline.md](patterns/streaming-etl-pipeline.md) | Generator-based extract/validate/batch-load with rejected-row tracking |
| [patterns/logging-setup.md](patterns/logging-setup.md) | `dictConfig` entry-point setup, env-driven level, JSON formatter |
| [patterns/testing-pytest.md](patterns/testing-pytest.md) | Fixtures, `conftest.py`, `tmp_path`, parametrize, `pytest.raises` |
| [patterns/error-handling-retry.md](patterns/error-handling-retry.md) | Transient vs permanent errors, typed retry decorator with backoff |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/python-toolchain.yaml](specs/python-toolchain.yaml) | Required `pyproject.toml` tables/keys and their validation rules |

### Examples

| File | Purpose |
|------|---------|
| [examples/tests/python-kb-checks.json](examples/tests/python-kb-checks.json) | Verified input/expected behaviors backing KB claims |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Laziness** | Generators keep memory flat regardless of file size; materialize only at the sink |
| **Explicit types** | Hints + mypy strict catch schema/shape bugs before data is loaded |
| **Fail loudly, retry narrowly** | Catch specific exceptions, chain causes, retry only transient errors |
| **Configure once** | Logging and dependencies are configured at the entry point / `pyproject.toml` |
| **Reproducibility** | `uv.lock` + `requires-python` + CI `uv sync --locked` |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/packaging-venv.md, concepts/type-hints.md, concepts/pathlib-file-io.md, concepts/dataclasses.md |
| **Intermediate** | concepts/generators-iterators.md, concepts/context-managers.md, concepts/exceptions.md, concepts/logging.md, patterns/project-setup-uv.md, patterns/testing-pytest.md |
| **Advanced** | patterns/streaming-etl-pipeline.md, patterns/error-handling-retry.md, patterns/logging-setup.md, specs/python-toolchain.yaml |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| kb-architect | index.md, specs/python-toolchain.yaml | Audit/extend this domain |
| Any coding agent | patterns/*.md, quick-reference.md | Write pipeline code, tests and project config |
