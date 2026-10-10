# Docker Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-10-09

## Pinned Versions (checked 2026-10-09)

| Component | Reference | Notes |
|-----------|-----------|-------|
| Python base | `python:3.12-slim-trixie` | Builder and runtime stages must match |
| uv | `ghcr.io/astral-sh/uv:0.13.0` | `COPY --from=... /uv /uvx /bin/` |
| Warehouse DB | `postgres:18` | Volume at `/var/lib/postgresql` (18+) |
| Airflow | `apache/airflow:3.3.2` | Metadata DB `postgres:16` as in official file |
| dbt | `dbt-core~=1.11.0`, `dbt-postgres~=1.11.0` | ghcr.io images stop at `1.9.latest` |

## docker compose Commands

| Task | Command |
|------|---------|
| Validate / render config (no daemon) | `docker compose config --quiet` |
| Start in background, rebuild images | `docker compose up -d --build` |
| Block until healthy | `docker compose up -d --wait postgres` |
| Status incl. exited + exit codes | `docker compose ps -a` |
| Follow logs of one service | `docker compose logs -f --tail=200 airflow-scheduler` |
| Shell / command in running container | `docker compose exec postgres psql -U dw -d warehouse` |
| One-off container, removed after | `docker compose run --rm dbt build` |
| Start an optional (profiled) service | `docker compose --profile tools run --rm dbt debug` |
| Stop + remove containers/networks | `docker compose down` |
| ...and delete named volumes (data!) | `docker compose down -v` |
| Live rebuild on file change | `docker compose watch` (needs `develop.watch`) |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Persist Postgres data | Named volume |
| Edit DAGs / dbt models from the host | Bind mount |
| Init scripts, config files | Bind mount `:ro` |
| Wait for DB before starting app | `depends_on` + `condition: service_healthy` |
| One-shot migration/init before others | `condition: service_completed_successfully` |
| Optional tool (dbt CLI, adminer, ingest job) | `profiles: [tools]` + `run --rm` |
| Non-secret config | `.env` interpolation / `environment:` |
| Passwords | `secrets:` + `*_FILE` env vars |
| Python deps in image | uv multi-stage (`--locked --no-install-project`) |
| dbt inside Airflow | Separate venv in a derived Airflow image |
| Airflow executor locally | `LocalExecutor` (no redis/worker) |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `DB_HOST: localhost` inside a container | `DB_HOST: postgres` (service name), port 5432 |
| Short `depends_on: [postgres]` | Long form with `service_healthy` |
| `test: ["CMD", "pg_isready -U $USER"]` | `["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]` |
| `postgres:18` mounted at `/var/lib/postgresql/data` | Mount at `/var/lib/postgresql` |
| Expect init scripts to rerun | They run only on an empty data dir: `down -v` |
| `COPY . .` before installing deps | Copy lockfile/manifest first, source last |
| `FROM python:latest`, `image: x:latest` | Pin tags (digests for full immutability) |
| `POSTGRES_PASSWORD: secret` committed | `POSTGRES_PASSWORD_FILE` + git-ignored secret file |
| Running as root | `USER 10001` / `AIRFLOW_UID=$(id -u)` |
| `CMD python app.py` (shell form) | `CMD ["python", "app.py"]` |
| `docker compose restart` after editing yaml | `docker compose up -d` (recreates) |
| `version: "3.8"` | Omit (obsolete) |

## Related Documentation

| Topic | Path |
|-------|------|
| Getting Started | `concepts/container-lifecycle.md` |
| Stack troubleshooting | `patterns/compose-dev-workflow.md` |
| Compose spec rules | `specs/compose-stack.yaml` |
| Python project setup | `../python/patterns/project-setup-uv.md` |
| Full Index | `index.md` |
