# Postgres Warehouse Service

> **Purpose**: Run the warehouse Postgres with persistent data, readiness healthcheck, file-based password and first-boot init scripts
> **MCP Validated**: 2026-10-09

## When to Use

- The local warehouse database that ingestion writes to and dbt transforms
- Any stack where other services must wait for Postgres to accept connections
- Bootstrapping schemas/roles (`raw`, `staging`, `marts`) reproducibly on a fresh volume

## Implementation

```yaml
# compose.yaml (excerpt)
name: dw

services:
  postgres:
    image: postgres:18                    # pin the major; 18.x patch updates are safe
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-dw}
      POSTGRES_DB: ${POSTGRES_DB:-warehouse}
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
      TZ: UTC
    secrets: [pg_password]
    ports:
      - "127.0.0.1:${PG_HOST_PORT:-5433}:5432"   # 5433 avoids clashing with a host Postgres
    volumes:
      - pgdata:/var/lib/postgresql               # PG 18+ volume path
      - ./postgres/initdb:/docker-entrypoint-initdb.d:ro
    shm_size: 128mb                              # default 64MB can break parallel queries
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
    restart: unless-stopped

volumes:
  pgdata: {}

secrets:
  pg_password:
    file: ./secrets/pg_password.txt
```

```sql
-- postgres/initdb/01-schemas.sql  (runs as POSTGRES_USER against POSTGRES_DB)
CREATE SCHEMA IF NOT EXISTS raw;       -- landing tables written by Python ingestion
CREATE SCHEMA IF NOT EXISTS staging;   -- dbt staging models
CREATE SCHEMA IF NOT EXISTS marts;     -- dbt marts consumed by BI
```

```bash
#!/usr/bin/env bash
# postgres/initdb/02-roles.sh -- .sh files run in name order after the .sql above
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-'EOSQL'
  DO $$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reporting') THEN
      CREATE ROLE reporting NOLOGIN;
    END IF;
  END $$;
  GRANT USAGE ON SCHEMA marts TO reporting;
  ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO reporting;
EOSQL
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `POSTGRES_PASSWORD` / `_FILE` | none (required) | Superuser password; `_FILE` reads it from a secret |
| `POSTGRES_USER` | `postgres` | Superuser created at init (also supports `_FILE`) |
| `POSTGRES_DB` | value of `POSTGRES_USER` | Default database created at init |
| `PGDATA` (18+) | `/var/lib/postgresql/18/docker` | Mount the volume at `/var/lib/postgresql` |
| `PGDATA` (<= 17) | `/var/lib/postgresql/data` | Mount the volume at `/var/lib/postgresql/data` |
| `/docker-entrypoint-initdb.d` | empty | `*.sql`, `*.sql.gz`, `*.sh`; run **only if the data dir is empty** |
| `shm_size` | `64mb` | Docker Hub recommends raising it under Compose |

## Example Usage

```bash
mkdir -p secrets && openssl rand -base64 24 > secrets/pg_password.txt
echo "secrets/" >> .gitignore
docker compose up -d --wait postgres                     # returns once healthy
docker compose exec postgres psql -U dw -d warehouse -c '\dn'
psql "postgresql://dw:$(cat secrets/pg_password.txt)@localhost:5433/warehouse"  # from host

# changed an init script? it only runs on an EMPTY volume:
docker compose down -v && docker compose up -d --wait postgres   # destroys data
```

## See Also

- [volumes-bind-mounts](../concepts/volumes-bind-mounts.md)
- [compose-services-healthchecks](../concepts/compose-services-healthchecks.md)
- [env-vars-secrets](../concepts/env-vars-secrets.md)
- [compose-dev-workflow](../patterns/compose-dev-workflow.md)
