# Compose Dev Workflow and Troubleshooting

> **Purpose**: Day-to-day commands to start, inspect, debug and reset the local data stack, plus fixes for the usual failures
> **MCP Validated**: 2026-10-09

## When to Use

- Bringing the stack up/down, rebuilding after code or dependency changes
- A service is unhealthy, exits immediately, or cannot reach Postgres
- Resetting state (fresh database, re-running init scripts) on purpose

## Implementation

```makefile
# Makefile -- thin wrappers so everyone runs the same commands (recipes use TABs)
COMPOSE ?= docker compose

.PHONY: config up down reset build logs ps psql ingest dbt shell

config:            ## validate + render the fully interpolated model
	$(COMPOSE) config --quiet && $(COMPOSE) config --services

up:                ## build + start core services in the background
	$(COMPOSE) up -d --build && $(COMPOSE) ps

down:              ## stop and remove containers + networks (keeps volumes)
	$(COMPOSE) down --remove-orphans

reset:             ## DESTRUCTIVE: also delete named volumes (DB data)
	$(COMPOSE) down -v --remove-orphans

build:             ## rebuild images, pulling newer base layers
	$(COMPOSE) build --pull

logs:              ## follow logs, e.g. make logs s=airflow-scheduler
	$(COMPOSE) logs -f --tail=200 $(s)

ps:
	$(COMPOSE) ps -a

psql:
	$(COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

ingest:            ## one-off job (profile "jobs")
	$(COMPOSE) --profile jobs run --rm ingest

dbt:               ## e.g. make dbt a="build --select staging+"
	$(COMPOSE) --profile tools run --rm dbt $(a)

shell:             ## shell in a running service, e.g. make shell s=postgres
	$(COMPOSE) exec $(s) bash
```

```text
compose.yaml layout for this project (single file, one project name)
  name: dw
  services:  postgres | airflow-db | airflow-init | airflow-apiserver |
             airflow-scheduler | airflow-dag-processor | ingest (jobs) | dbt (tools)
  volumes:   pgdata | airflow-db
  secrets:   pg_password
  .env:      POSTGRES_USER, POSTGRES_DB, PG_HOST_PORT, DW_PASSWORD, AIRFLOW_UID
```

## Configuration

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Bind for 0.0.0.0:5432 failed: port is already allocated` | Host Postgres / other stack on the port | Publish `5433:5432` or stop the other service |
| Init scripts / new `POSTGRES_*` values ignored | Volume already initialized | `docker compose down -v` (wipes data) |
| `connection refused` from a service at startup | Short `depends_on`, no healthcheck | `condition: service_healthy` |
| `Connection refused` to `localhost:5433` from a container | `localhost` = the container itself; 5433 is the host port | `host: postgres`, port `5432` |
| `dependency failed to start: ... is unhealthy` | Healthcheck failing | `docker inspect --format '{{json .State.Health}}' <container>` |
| Code change not reflected | Image not rebuilt | `up -d --build` (or `docker compose watch` with `develop.watch`) |
| `.env` edit not applied | Container not recreated | `docker compose up -d` (not `restart`) |
| `Permission denied` on bind-mounted dirs (Linux) | Container UID != host UID | Set `AIRFLOW_UID=$(id -u)` / `user:` |
| Container `Exited (137)` | OOM kill or `SIGKILL` after timeout | Raise Docker memory (Airflow wants >= 4 GB) |
| `the attribute version is obsolete` | Legacy `version:` key | Delete it |
| `Cannot connect to the Docker daemon` | Engine not running | Start Docker Desktop / `colima start` |

## Example Usage

```bash
docker compose config --quiet                     # syntax + interpolation check (no daemon needed)
docker compose config --services                  # services active without profiles
docker compose --profile tools config --services  # ...including the dbt service
docker compose up -d --build                      # build + start in background
docker compose up -d --wait postgres              # block until postgres is healthy
docker compose logs -f airflow-scheduler          # follow one service
docker compose exec postgres pg_isready           # run inside a running container
docker compose run --rm --no-deps dbt debug       # one-off, skip starting dependencies
docker compose cp postgres:/tmp/dump.sql ./dump.sql
docker compose top && docker compose stats --no-stream
docker system df                                  # disk used by images/volumes/cache
docker builder prune -f && docker image prune -f  # reclaim space (keeps volumes)
```

## See Also

- [container-lifecycle](../concepts/container-lifecycle.md)
- [compose-services-healthchecks](../concepts/compose-services-healthchecks.md)
- [networking](../concepts/networking.md)
- [postgres-service](../patterns/postgres-service.md)
