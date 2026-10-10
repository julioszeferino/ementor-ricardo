# Packaging and Virtual Environments

> **Purpose**: Isolate dependencies per project and declare them in a single `pyproject.toml`
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A virtual environment (`.venv`) is an isolated interpreter + site-packages so each
project pins its own dependency versions. `pyproject.toml` is the standard file for
project metadata (`[project]`), build backend (`[build-system]`), dev-only
dependencies (`[dependency-groups]`, PEP 735) and tool config (`[tool.*]`). uv
creates the venv, resolves dependencies into a cross-platform `uv.lock`, and
records the interpreter version in `.python-version`.

## The Pattern

```toml
# pyproject.toml
[project]
name = "projeto-data-warehouse"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "polars>=1.0",
    "pydantic>=2.7",
]

[project.optional-dependencies]      # published extras: pip install pkg[aws]
aws = ["boto3>=1.34"]

[dependency-groups]                  # local-only, never published (PEP 735)
dev = ["pytest>=8", "ruff>=0.6", "mypy>=1.11"]

[project.scripts]
dw-load = "dw.cli:main"              # console entry point

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```text
src/dw/__init__.py      <- "src layout": tests import the installed package,
src/dw/cli.py              not files that happen to be on cwd
tests/test_cli.py
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `uv init --package dw` | Project with src layout + pyproject | `--package` adds build system |
| `uv add polars` | Added to `[project].dependencies` | Updates `uv.lock` and `.venv` |
| `uv add --dev pytest` | Added to `[dependency-groups].dev` | `dev` group synced by default |
| `uv sync` | `.venv` matches lockfile | Creates venv if missing |
| `uv run pytest` | Runs inside project venv | No manual activation needed |
| `python -m venv .venv` | Plain stdlib venv | Fallback without uv |
| `uv.lock` | Exact resolved versions | Commit it; never edit by hand |

## Common Mistakes

### Wrong

```bash
pip install pandas            # into the global/system interpreter
pip freeze > requirements.txt # mixes direct and transitive deps, no dev split
```

### Correct

```bash
uv add pandas                 # declared in pyproject, locked in uv.lock
uv add --dev pytest ruff mypy
uv sync --locked              # CI: fail if lockfile is out of date
```

## Related

- [type-hints](../concepts/type-hints.md)
- [project-setup-uv](../patterns/project-setup-uv.md)
