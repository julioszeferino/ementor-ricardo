# Profiles, Targets and env_var

> **Purpose**: Connect dbt to the warehouse Postgres per environment (dev/prod) without secrets in git
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

`profiles.yml` holds connection details. A **profile** (`dw`) contains **outputs**
(targets); `target:` picks the default and `--target` overrides it. Every value can use
Jinja, so `env_var('NAME', 'default')` keeps the file committable. `target.name`,
`target.schema` etc. are available in models and macros -- this is how prod-only logic
(e.g. schema naming) works. dbt looks for `profiles.yml` in `--profiles-dir`, then
`DBT_PROFILES_DIR`, then the current directory, then `~/.dbt/`.

## The Pattern

```yaml
# dbt/profiles.yml -- committed: only env_var() lookups, no secrets
dw:
  target: "{{ env_var('DBT_TARGET', 'dev') }}"
  outputs:
    dev:                                       # laptop -> published port of compose postgres
      type: postgres
      host: "{{ env_var('DBT_HOST', 'localhost') }}"
      port: "{{ env_var('DBT_PORT', '5433') | as_number }}"
      user: "{{ env_var('DBT_USER') }}"        # no default -> error if unset
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: "{{ env_var('DBT_DBNAME', 'warehouse') }}"
      schema: "{{ env_var('DBT_SCHEMA', 'dbt_dev') }}"   # personal sandbox schema
      threads: "{{ env_var('DBT_THREADS', '4') | as_number }}"
      connect_timeout: 10
    prod:                                      # inside compose / Airflow -> service DNS name
      type: postgres
      host: "{{ env_var('DBT_HOST', 'postgres') }}"
      port: "{{ env_var('DBT_PORT', '5432') | as_number }}"
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: "{{ env_var('DBT_DBNAME', 'warehouse') }}"
      schema: analytics                        # fallback only; folders set +schema
      threads: "{{ env_var('DBT_THREADS', '4') | as_number }}"
```

```bash
export DBT_USER=dw DBT_PASSWORD=...           # or a git-ignored .env loaded by your shell
dbt debug                                     # validates profile + connection
dbt build --target prod                       # Airflow / compose run
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `env_var('DBT_USER')` unset | `Parsing Error: Env var required but not provided: 'DBT_USER'` | Verified with `dbt parse` |
| `env_var('X', 'd')` | `'d'` when unset | Always a **string** |
| `"{{ ... \| as_number }}"` | integer | Needed for `port`, `threads` |
| `DBT_ENV_SECRET_*` | Scrubbed from logs | Only in profiles.yml / packages.yml |
| `--target prod` / `DBT_TARGET=prod` | Uses `prod` output | `target.name == 'prod'` in Jinja |
| `DBT_PROFILES_DIR=/usr/app` | Where profiles.yml is | 1.11 also accepts `DBT_ENGINE_PROFILES_DIR` (new prefix) |
| Postgres keys | `host port user password dbname schema threads` | Optional: `keepalives_idle`, `sslmode`, `search_path`, `role` |

## Common Mistakes

### Wrong

```yaml
dw:
  outputs:
    dev:
      host: localhost
      port: {{ env_var('DBT_PORT') }}   # unquoted Jinja -> invalid YAML
      password: s3cret                  # secret committed to git
```

### Correct

```yaml
dw:
  outputs:
    dev:
      host: "{{ env_var('DBT_HOST', 'localhost') }}"
      port: "{{ env_var('DBT_PORT', '5433') | as_number }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
```

Inside a container `localhost` is the container itself: use the service name
(`postgres:5432`), see `../docker/concepts/networking.md`.

## Related

- [project-structure](../concepts/project-structure.md)
- [project-setup-commands](../patterns/project-setup-commands.md)
- [dbt-runner-container (docker KB)](../../docker/patterns/dbt-runner-container.md)
- [env-vars-secrets (docker KB)](../../docker/concepts/env-vars-secrets.md)
