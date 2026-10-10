# Project Setup with uv, ruff and mypy

> **Purpose**: Bootstrap a reproducible Python 3.12+ project with locked deps, linting, formatting and type checking
> **MCP Validated**: 2026-10-09

## When to Use

- Starting a new pipeline/service repository or a new package inside the warehouse repo
- Replacing `requirements.txt` + ad-hoc `pip` installs with a lockfile
- Enforcing the same quality gates locally and in CI

## Implementation

```bash
# 1. Create the project (src layout, build backend, .python-version, git-ignored .venv)
uv init --package --python 3.12 dw
cd dw

# 2. Runtime and dev dependencies
uv add polars pydantic
uv add --dev pytest pytest-cov ruff mypy

# 3. Quality gates
uv run ruff check --fix .
uv run ruff format .
uv run mypy src
uv run pytest
```

```toml
# pyproject.toml (tool sections appended to what `uv init` generated)
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E", "F",   # pycodestyle errors, pyflakes (ruff defaults)
    "I",        # isort import ordering
    "B",        # flake8-bugbear (mutable defaults, loop closures...)
    "UP",       # pyupgrade: modern syntax (X | None, list[int])
    "SIM",      # flake8-simplify
    "PTH",      # prefer pathlib over os.path
    "LOG", "G", # logging misuse, f-strings in log calls
    "RUF",      # ruff-specific rules
]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]           # assert is fine in tests

[tool.ruff.format]
quote-style = "double"
docstring-code-format = true

[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
mypy_path = "src"

[[tool.mypy.overrides]]
module = ["some_untyped_lib.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "--import-mode=importlib"]
```

```yaml
# .github/workflows/ci.yml (job steps)
- uses: astral-sh/setup-uv@v6
- run: uv sync --locked            # fails if uv.lock is stale
- run: uv run ruff format --check .
- run: uv run ruff check .
- run: uv run mypy src
- run: uv run pytest --cov=src
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `tool.ruff.line-length` | `88` | Max line length for lint (E501) and formatter |
| `tool.ruff.target-version` | from `requires-python` | Minimum Python syntax ruff may emit/suggest |
| `tool.ruff.lint.select` | `["E4","E7","E9","F"]` | Rule families to enable |
| `tool.mypy.strict` | `false` | Enables all optional strictness flags |
| `tool.uv.default-groups` | `["dev"]` | Dependency groups installed by `uv sync` |
| `requires-python` | set by `uv init` | Constrains resolution and interpreter |

## Example Usage

```bash
uv run python -m dw            # run package entry point inside the venv
uv lock --upgrade-package polars   # bump one dependency, keep others pinned
uv sync --no-dev               # production image: runtime deps only
uv run --with ipython ipython  # one-off tool without adding it to the project
uvx ruff check .               # run a tool in an ephemeral env (no project needed)
```

## See Also

- [testing-pytest](../patterns/testing-pytest.md)
- [packaging-venv](../concepts/packaging-venv.md)
