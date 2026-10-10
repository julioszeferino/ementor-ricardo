# Sources and Freshness

> **Purpose**: Declare the raw tables loaded by Python ingestion as dbt sources and monitor how stale they are
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A **source** names a table dbt does not build (here: tables in schema `raw` written by
the Python ingestion). Models read it with `{{ source('erp', 'vendas') }}`, which puts
the raw table in the DAG and lineage docs and lets you test it. **Freshness** compares
`max(loaded_at_field)` with now; since 1.10, `freshness` and `loaded_at_field` live
under `config:` (top-level is the legacy form). Use `source()` only in staging models.

## The Pattern

```yaml
# models/staging/erp/_erp__sources.yml
sources:
  - name: erp                      # logical name used in source('erp', ...)
    description: "Arquivos de data/ carregados pela ingestao Python no schema raw"
    database: warehouse
    schema: raw                    # defaults to the source name if omitted
    config:
      loaded_at_field: _loaded_at  # timestamp column set by the ingestion
      freshness:
        warn_after: {count: 24, period: hour}
        error_after: {count: 48, period: hour}
    tables:
      - name: clientes
        columns:
          - name: id
            data_tests: [unique, not_null]
      - name: produtos
      - name: vendas
        config:
          freshness:               # table-level overrides source-level
            warn_after: {count: 6, period: hour}
            error_after: {count: 24, period: hour}
```

```bash
dbt source freshness                       # sources only; writes target/sources.json
dbt source freshness --select source:erp.vendas
dbt build --select "source_status:fresher+" --state state/   # only what got new data
dbt test --select "source:erp"             # tests declared on source columns
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `source('erp', 'vendas')` | `"warehouse"."raw"."vendas"` | Errors at parse if undeclared |
| `loaded_at_field` absent | Uses warehouse metadata where supported | Postgres: declare it explicitly |
| `loaded_at_query: "select max(...)"` | Custom freshness SQL (1.10+) | Cannot be combined with `loaded_at_field` |
| `freshness: null` on a table | Excluded from freshness | e.g. static lookup tables |
| `filter: "_loaded_at > now() - interval '7 days'"` | WHERE on freshness query | Speeds up large tables |
| `dbt freshness` (newer) | Checks sources **and** models with freshness | `dbt source freshness` still supported |
| `identifier: tb_vendas_v2` | Physical table name differs from `name` | Keep `name` stable for refs |

## Common Mistakes

### Wrong

```sql
-- hardcoded relation: no lineage, no freshness, breaks when schema/db changes
select * from raw.vendas
```

### Correct

```sql
select * from {{ source('erp', 'vendas') }}
```

The ingestion must write the `_loaded_at` column (e.g. `timestamptz default now()`)
or freshness has nothing to measure -- see the Python ETL pattern.

## Related

- [models-ref-dag](../concepts/models-ref-dag.md)
- [staging-model](../patterns/staging-model.md)
- [schema-yml-tests](../patterns/schema-yml-tests.md)
- [streaming-etl-pipeline (python KB)](../../python/patterns/streaming-etl-pipeline.md)
