# Environment Variables, .env and Secrets

> **Purpose**: Configure services without hardcoding credentials, and know which value wins
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

Two different mechanisms are often confused. The project `.env` file (next to
`compose.yaml`) feeds **interpolation** of `${VAR}` inside the Compose file; it does not
reach containers by itself. `environment:` and `env_file:` set variables **inside**
containers. For passwords, prefer Compose `secrets`, mounted read-only at
`/run/secrets/<name>`; official images such as `postgres` read `*_FILE` variables.

## The Pattern

```dotenv
# .env  (git-ignored; commit a .env.example with dummy values)
POSTGRES_USER=dw
POSTGRES_DB=warehouse
PG_HOST_PORT=5433
```

```yaml
services:
  postgres:
    image: postgres:18
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?set POSTGRES_USER in .env}   # fail fast if unset
      POSTGRES_DB: ${POSTGRES_DB:-warehouse}                       # default if unset/empty
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password             # image reads the file
    secrets: [pg_password]
    ports:
      - "127.0.0.1:${PG_HOST_PORT:-5433}:5432"
  ingest:
    build: ./ingest
    env_file:
      - path: ./ingest/.env          # loaded INTO the container
        required: false              # ok if the file does not exist
    environment:
      DB_HOST: postgres              # environment: beats env_file: for same key
      LOG_LEVEL: "INFO"

secrets:
  pg_password:
    file: ./secrets/pg_password.txt  # git-ignored file containing only the password
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `${VAR}` | Value from shell or `.env` | Shell env overrides `.env` |
| `${VAR:-default}` | `default` if unset **or empty** | `${VAR-default}`: only if unset |
| `${VAR:?msg}` | Error with `msg` if unset/empty | Use for required credentials |
| `$$VAR` | Literal `$VAR` passed to container | Needed in healthcheck/command strings |
| `--env-file other.env` | Replaces `.env` for interpolation | Per-environment configs |
| Precedence (high -> low) | `run -e` > interpolated `environment`/`env_file` > `environment` > `env_file` > image `ENV` | Per Docker docs |
| `secrets: [x]` | File at `/run/secrets/x`, mode 0444 | Not visible in `docker inspect` env |
| `docker compose config` | Fully interpolated model | Prints secrets in plain text -- don't paste it |

## Common Mistakes

### Wrong

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: supersecret   # committed to git, visible in `docker inspect`
      LOAD_EXAMPLES: true              # unquoted YAML boolean
```

### Correct

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
      LOAD_EXAMPLES: "true"            # quote booleans
    secrets: [pg_password]
secrets:
  pg_password:
    file: ./secrets/pg_password.txt
```

## Related

- [compose-services-healthchecks](../concepts/compose-services-healthchecks.md)
- [dockerfile-best-practices](../concepts/dockerfile-best-practices.md)
- [postgres-service](../patterns/postgres-service.md)
