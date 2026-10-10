# Project Structure and dbt_project.yml

> **Purpose**: Lay out a dbt Core project and configure resources hierarchically from `dbt_project.yml`
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A dbt project is a folder with a `dbt_project.yml` plus resource folders (models, seeds,
snapshots, tests, macros). `dbt_project.yml` names the project, points to the
connection **profile**, and sets configs by folder path with the `+` prefix; a model's
own `config()` block overrides the folder config. In this repo the project lives in
`dbt/` and is named `dw`, matching the `dw` profile used by the docker KB.

## The Pattern

```yaml
# dbt/dbt_project.yml
name: dw
version: "1.0.0"
config-version: 2
profile: dw                                   # top-level key in profiles.yml
require-dbt-version: [">=1.11.0", "<1.12.0"]  # fail fast on the wrong dbt

model-paths: ["models"]
seed-paths: ["seeds"]
snapshot-paths: ["snapshots"]
test-paths: ["tests"]
macro-paths: ["macros"]
clean-targets: ["target", "dbt_packages"]     # removed by `dbt clean`

vars:
  data_inicio_calendario: "2020-01-01"        # read with var('...')

models:
  dw:                                         # must equal `name:`
    +persist_docs: {relation: true, columns: true}
    staging:                                  # = models/staging/
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
      +schema: intermediate
    marts:
      +materialized: table
      +schema: marts

seeds:
  dw:
    +schema: staging
snapshots:
  dw:
    +schema: snapshots
```

```text
dbt/
├── dbt_project.yml     packages.yml   package-lock.yml   profiles.yml
├── models/
│   ├── staging/erp/    _erp__sources.yml  _erp__models.yml  stg_erp__*.sql
│   ├── intermediate/   int_*.sql
│   └── marts/core/     _core__models.yml  dim_*.sql  fct_*.sql
├── snapshots/          snap_erp__clientes.yml
├── seeds/              uf_regioes.csv  _seeds.yml
├── macros/             generate_schema_name.sql  *.sql
├── tests/              assert_*.sql (singular data tests)
├── target/  logs/  dbt_packages/          # generated -> .gitignore
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `+materialized: view` under `staging:` | All models in `models/staging/**` are views | `+` marks a config, not a subfolder |
| `{{ config(materialized='table') }}` in a .sql | Overrides folder config | Most specific wins |
| `+schema: marts` | Custom schema (see generate_schema_name) | Default result is `<target_schema>_marts` |
| `require-dbt-version` | Error on other versions | Keep aligned with `dbt-core~=1.11.0` pin |
| `flags:` block | Opt-in behavior changes | e.g. `require_unique_project_resource_names` (1.11) |
| `dbt clean` | Deletes `clean-targets` | Then `dbt deps` again |

## Common Mistakes

### Wrong

```yaml
models:
  my_project:          # does not match `name: dw` -> configs silently not applied
    staging:
      materialized: view   # no `+`; works today but ambiguous with subfolder names
```

### Correct

```yaml
models:
  dw:
    staging:
      +materialized: view
```

Also: never commit `target/`, `logs/` or `dbt_packages/`; do commit `package-lock.yml`.

## Related

- [profiles-targets](../concepts/profiles-targets.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [project-setup-commands](../patterns/project-setup-commands.md)
