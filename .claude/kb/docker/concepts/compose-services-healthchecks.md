# Compose Services, depends_on and Healthchecks

> **Purpose**: Start a multi-service stack in the right order by waiting for real readiness, not just container start
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A `compose.yaml` (Compose Specification) declares `services`, `volumes`, `networks`
and `secrets`; the top-level `version:` key is obsolete and only produces a warning.
Short-form `depends_on` only waits for the dependency container to **start**. A
Postgres container starts seconds before it accepts connections, so pair a
`healthcheck` on the dependency with `condition: service_healthy` on the dependent,
and `service_completed_successfully` for one-shot init/migration jobs.

## The Pattern

```yaml
name: dw                                   # project name (prefix for volumes/networks)

services:
  postgres:
    image: postgres:18
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s                    # failures here don't count toward retries
      start_interval: 1s                   # faster probing during start_period
  migrate:
    build: ./ingest
    command: ["python", "-m", "dw.migrate"]
    depends_on:
      postgres:
        condition: service_healthy
  ingest:
    build: ./ingest
    depends_on:
      postgres:
        condition: service_healthy
        restart: true                      # restart ingest if postgres is restarted
      migrate:
        condition: service_completed_successfully   # exit code 0 required
  adminer:
    image: adminer:6                       # web DB browser at http://localhost:8081
    ports: ["8081:8080"]
    profiles: [tools]                      # only started with --profile tools
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `depends_on: [postgres]` | Waits for container start only | Equals `service_started` |
| `condition: service_healthy` | Waits until healthcheck passes | Dependency needs a `healthcheck` |
| `condition: service_completed_successfully` | Waits for exit code 0 | Init/migration containers |
| `required: false` | Warn instead of fail if dep missing | Compose >= 2.20 |
| `test: ["CMD", ...]` | Exec directly, no shell | No `$VAR` expansion |
| `test: ["CMD-SHELL", "..."]` | Run via `/bin/sh -c` | Use `$$VAR` to defer to container env |
| Healthcheck defaults | interval 30s, timeout 30s, retries 3, start_period 0s, start_interval 5s | Same as Dockerfile `HEALTHCHECK`; `start_interval` needs Engine >= 25 |
| `docker compose up -d --wait` | Returns when services are running/healthy | Great for scripts and CI |
| `profiles: [x]` | Service off unless `--profile x` | Optional tools (BI, CLI, debug) |

## Common Mistakes

### Wrong

```yaml
version: "3.8"                 # obsolete, warning only
services:
  ingest:
    depends_on: [postgres]     # ingest crashes: "connection refused" on first run
  postgres:
    image: postgres:18
    healthcheck:
      test: ["CMD", "pg_isready -U $POSTGRES_USER"]   # CMD form: no shell, one bogus argv
```

### Correct

```yaml
services:
  ingest:
    depends_on:
      postgres:
        condition: service_healthy
  postgres:
    image: postgres:18
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      retries: 10
```

## Related

- [networking](../concepts/networking.md)
- [env-vars-secrets](../concepts/env-vars-secrets.md)
- [postgres-service](../patterns/postgres-service.md)
