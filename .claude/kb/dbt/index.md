# dbt Knowledge Base

> **Purpose**: dbt Core 1.11 + dbt-postgres for the warehouse -- turning raw ingestion tables into tested staging views and a Kimball star schema (Postgres, orchestrated by Airflow, read by Metabase)
> **MCP Validated**: 2026-10-09

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/project-structure.md](concepts/project-structure.md) | Folder layout, `dbt_project.yml`, `+` configs, `require-dbt-version` |
| [concepts/profiles-targets.md](concepts/profiles-targets.md) | `profiles.yml` with `env_var`, `dev`/`prod` targets, `target.*` |
| [concepts/sources-freshness.md](concepts/sources-freshness.md) | `source()`, `raw` schema, freshness under `config:` (1.10+) |
| [concepts/models-ref-dag.md](concepts/models-ref-dag.md) | Models, `ref()`, the DAG and `--select` graph operators |
| [concepts/materializations.md](concepts/materializations.md) | view/table/incremental/ephemeral/MV; Postgres incremental strategies |
| [concepts/layered-architecture.md](concepts/layered-architecture.md) | staging -> intermediate -> marts, naming, `generate_schema_name` |
| [concepts/testing.md](concepts/testing.md) | Generic/singular data tests (`arguments:`), unit tests |
| [concepts/jinja-macros.md](concepts/jinja-macros.md) | Jinja syntax, macros, `var`, `target`, `run-operation` |
| [concepts/seeds-snapshots.md](concepts/seeds-snapshots.md) | CSV lookups; YAML snapshots (1.9+), meta columns, hard deletes |
| [concepts/documentation.md](concepts/documentation.md) | Descriptions, doc blocks, `persist_docs`, docs site, exposures |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/staging-model.md](patterns/staging-model.md) | Source YAML + `stg_erp__*` view with renaming/casting macros |
| [patterns/star-schema-marts.md](patterns/star-schema-marts.md) | `dim_*` + `fct_vendas` with `generate_surrogate_key`, `dim_data` spine |
| [patterns/incremental-fact-postgres.md](patterns/incremental-fact-postgres.md) | delete+insert fact with lookback, indexes, incremental unit test |
| [patterns/snapshot-scd2-dimension.md](patterns/snapshot-scd2-dimension.md) | Snapshot -> SCD2 `dim_clientes` + point-in-time fact join |
| [patterns/schema-yml-tests.md](patterns/schema-yml-tests.md) | Properties YAML: tests, severity, relationships, dbt_utils tests |
| [patterns/project-setup-commands.md](patterns/project-setup-commands.md) | Pins, `packages.yml`, run commands, CI, `state:modified`/`--defer` |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/dbt-project.yaml](specs/dbt-project.yaml) | Required keys/conventions for `dbt_project.yml`, `profiles.yml`, `packages.yml` |

### Examples

| File | Purpose |
|------|---------|
| [examples/tests/dbt-kb-checks.json](examples/tests/dbt-kb-checks.json) | dbt 1.11.15 parse/build behaviors backing KB claims |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Models are SELECTs** | dbt wraps them in DDL; `ref()`/`source()` build the DAG |
| **Layers** | `raw` (ingestion) -> `staging` views -> `intermediate` -> `marts` star schema |
| **Environments** | Same code, `--target dev\|prod`; prod lands in exact schemas |
| **Test everything** | PK/FK data tests on every model; unit tests for tricky logic |
| **History** | Snapshots capture SCD2 changes of overwritten sources |
| **Pin versions** | `dbt-core~=1.11.0`, `dbt-postgres~=1.11.0`, dbt_utils `<2.0.0` |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/project-structure.md, concepts/profiles-targets.md, concepts/models-ref-dag.md, concepts/sources-freshness.md, patterns/staging-model.md |
| **Intermediate** | concepts/materializations.md, concepts/layered-architecture.md, concepts/testing.md, concepts/jinja-macros.md, patterns/schema-yml-tests.md, patterns/star-schema-marts.md |
| **Advanced** | concepts/seeds-snapshots.md, patterns/snapshot-scd2-dimension.md, patterns/incremental-fact-postgres.md, patterns/project-setup-commands.md, specs/dbt-project.yaml |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| kb-architect | index.md, specs/dbt-project.yaml | Audit/extend this domain |
| Any coding agent | patterns/*.md, quick-reference.md | Write models, YAML and dbt commands under `dbt/` |
| Docker/Airflow work | ../docker/patterns/dbt-runner-container.md, ../docker/patterns/airflow-local-compose.md | Run dbt in containers / from Airflow |

Out of scope: dbt Cloud features (IDE, jobs, Semantic Layer/MetricFlow), dbt Fusion engine, Python models.
