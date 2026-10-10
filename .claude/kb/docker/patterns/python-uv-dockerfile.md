# Python App Dockerfile with uv

> **Purpose**: Package the Python ingestion code as a small, non-root, reproducible image built from `uv.lock`
> **MCP Validated**: 2026-10-09

## When to Use

- Containerizing the ingestion package (`src/dw`, console script `dw-load`) set up per the python KB
- Running the loader as a one-off/batch Compose service against the warehouse Postgres
- Any uv-managed project that needs fast rebuilds (deps cached separately from source)

## Implementation

```dockerfile
# syntax=docker/dockerfile:1
# ingest/Dockerfile -- build context = project root containing pyproject.toml + uv.lock
ARG PYTHON_VERSION=3.12

# ---------- stage 1: resolve and install into /app/.venv ----------
FROM python:${PYTHON_VERSION}-slim-trixie AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 1a. dependencies only -- cached until pyproject.toml / uv.lock change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# 1b. the project itself (non-editable => venv is self-contained)
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# ---------- stage 2: runtime without uv, compilers or source tree ----------
# Must match the builder base: the venv's python symlink points at /usr/local/bin.
FROM python:${PYTHON_VERSION}-slim-trixie AS runtime

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app
USER app
ENTRYPOINT ["dw-load"]
CMD ["--help"]
```

```gitignore
# .dockerignore (build context root)
.git
.venv
**/__pycache__
.mypy_cache
.pytest_cache
.ruff_cache
.env
.env.*
secrets/
data/
logs/
dags/
dbt/
postgres/
```

```yaml
# compose.yaml (excerpt) -- batch job, not a long-running service
services:
  ingest:
    build:
      context: .
      dockerfile: ingest/Dockerfile
    image: dw-ingest:dev
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_NAME: ${POSTGRES_DB:-warehouse}
      DB_USER: ${POSTGRES_USER:-dw}
      DB_PASSWORD_FILE: /run/secrets/pg_password  # app reads the password from this file
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    secrets: [pg_password]
    volumes:
      - ./data/landing:/data/landing:ro      # source files to ingest
    depends_on:
      postgres:
        condition: service_healthy
    profiles: [jobs]                         # not started by plain `up`
    restart: "no"
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `UV_COMPILE_BYTECODE` | `0` | `1` precompiles `.pyc`: faster startup, slower build |
| `UV_LINK_MODE` | `hardlink` | `copy` silences warnings when cache and venv are on different filesystems |
| `UV_NO_DEV` | unset | `1` skips `[dependency-groups].dev` (pytest, ruff, mypy) |
| `UV_PYTHON_DOWNLOADS` | `automatic` | `0` forces the image's system Python in both stages |
| `--locked` | off | Fail the build if `uv.lock` is out of sync with `pyproject.toml` |
| `--no-install-project` | off | Install deps only, so source edits don't bust the dependency layer |
| `--no-editable` | editable | Copy the project into the venv; the runtime stage needs no source |
| uv image tag | `latest` | Pin (`0.13.0`) or pin a digest for reproducible builds |

## Example Usage

```bash
docker compose build ingest                         # BuildKit caches /root/.cache/uv
docker compose run --rm ingest --source /data/landing/sales.csv
docker compose run --rm --entrypoint python ingest -c "import dw; print(dw.__file__)"
docker image ls dw-ingest                           # expect ~150-250 MB on slim
docker build --target builder -t dw-ingest:builder -f ingest/Dockerfile .   # debug stage 1
```

## See Also

- [project-setup-uv (python KB)](../../python/patterns/project-setup-uv.md)
- [packaging-venv (python KB)](../../python/concepts/packaging-venv.md)
- [dockerfile-best-practices](../concepts/dockerfile-best-practices.md)
- [images-layers-cache](../concepts/images-layers-cache.md)
