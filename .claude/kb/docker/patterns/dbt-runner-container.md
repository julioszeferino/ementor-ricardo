# dbt Runner Container (dbt-postgres)

> **Purpose**: Run dbt Core against the warehouse Postgres from a pinned container, configured only through environment variables
> **MCP Validated**: 2026-10-09

## When to Use

- Same dbt version for every developer and for CI, with no local Python setup
- Ad-hoc `dbt build/test/docs` runs against the Compose Postgres (`docker compose run --rm dbt ...`)
- A reference image for how Airflow invokes dbt (see the Airflow pattern's dbt venv)

## Implementation

```dockerfile
# syntax=docker/dockerfile:1
# dbt/Dockerfile
FROM python:3.12-slim-trixie

# dbt-core and dbt-postgres version independently since 1.8; pin both
ARG DBT_CORE_VERSION=1.11.0
ARG DBT_POSTGRES_VERSION=1.11.0
RUN pip install --no-cache-dir \
      "dbt-core~=${DBT_CORE_VERSION}" \
      "dbt-postgres~=${DBT_POSTGRES_VERSION}"

RUN groupadd --system --gid 10001 dbt \
 && useradd --system --uid 10001 --gid dbt --create-home dbt
USER dbt
WORKDIR /usr/app
ENV DBT_PROFILES_DIR=/usr/app \
    DBT_SEND_ANONYMOUS_USAGE_STATS=false
ENTRYPOINT ["dbt"]
CMD ["--version"]
```

```yaml
# dbt/profiles.yml -- committed: contains no secrets, only env_var() lookups
dw:
  target: docker
  outputs:
    docker:                                   # inside Compose: service DNS name
      type: postgres
      host: "{{ env_var('DBT_HOST', 'postgres') }}"
      port: "{{ env_var('DBT_PORT', '5432') | as_number }}"
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: "{{ env_var('DBT_DBNAME', 'warehouse') }}"
      schema: "{{ env_var('DBT_SCHEMA', 'staging') }}"
      threads: "{{ env_var('DBT_THREADS', '4') | int }}"
    local:                                    # from the host via the published port
      type: postgres
      host: localhost
      port: 5433
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: warehouse
      schema: staging
      threads: 4
```

```yaml
# compose.yaml (excerpt)
services:
  dbt:
    build: ./dbt
    image: dw-dbt:1.11
    environment:
      DBT_USER: ${POSTGRES_USER:-dw}
      DBT_PASSWORD: ${DW_PASSWORD:?set DW_PASSWORD}
      DBT_HOST: postgres
    volumes:
      - ./dbt:/usr/app                        # project, profiles.yml, target/, logs/
    depends_on:
      postgres:
        condition: service_healthy
    profiles: [tools]                         # run on demand only
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `DBT_PROFILES_DIR` | `~/.dbt` | Directory holding `profiles.yml`; set to the mounted project |
| `DBT_TARGET` / `--target` | `target:` in profile | Select `docker` vs `local` output |
| `env_var('X', 'default')` | error if unset and no default | Quote the whole Jinja string in YAML |
| `\| as_number` / `\| int` | strings | Required for `port` and `threads` |
| `DBT_ENV_SECRET_*` | - | Scrubbed from logs; only usable in `profiles.yml`/`packages.yml`, no filters |
| Official image | `ghcr.io/dbt-labs/dbt-postgres:<tag>` | Newest tag on ghcr.io is `1.9.0` / `1.9.latest` (checked 2026-10-09) |
| Version pins | `~=1.11.0` | dbt-core 1.11.15 + dbt-postgres 1.11.0 resolved cleanly; 1.12.5 needed a pre-release dep |

## Example Usage

```bash
docker compose build dbt
docker compose run --rm dbt debug                 # checks profile + connection
docker compose run --rm dbt deps                  # writes dbt_packages/ into ./dbt
docker compose run --rm dbt build --select staging+
docker compose run --rm dbt run --target docker --vars '{run_date: 2026-10-09}'
docker compose run --rm --entrypoint bash dbt   # interactive shell

# official image alternative (older dbt; WORKDIR /usr/app/dbt, ENTRYPOINT dbt, runs as root):
docker run --rm --network dw_default -v "$PWD/dbt:/usr/app/dbt" \
  -v "$PWD/dbt/profiles.yml:/root/.dbt/profiles.yml" \
  ghcr.io/dbt-labs/dbt-postgres:1.9.latest debug
```

Linux hosts: the container writes `target/` and `logs/` as UID 10001; add
`user: "${UID_GID:-1000:1000}"` to the service if you need host-owned files.

## See Also

- [airflow-local-compose](../patterns/airflow-local-compose.md)
- [postgres-service](../patterns/postgres-service.md)
- [env-vars-secrets](../concepts/env-vars-secrets.md)
- [networking](../concepts/networking.md)
