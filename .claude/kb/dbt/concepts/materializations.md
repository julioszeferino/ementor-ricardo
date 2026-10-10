# Materializations (Postgres)

> **Purpose**: Choose how each model is persisted -- view, table, incremental, ephemeral, materialized view -- and the incremental strategy on Postgres
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

The materialization decides the DDL/DML dbt wraps around a model's SELECT. Start with
**view**, move to **table** when queries get slow, and to **incremental** only when the
table build itself gets slow. **Ephemeral** models are not created in the database; they
are inlined as CTEs into the models that `ref()` them. dbt-postgres supports the
incremental strategies `append` (default without `unique_key`), `delete+insert` (default
with `unique_key`), `merge` (uses SQL `MERGE`, Postgres 15+) and `microbatch`.

## The Pattern

```sql
-- models/marts/core/fct_vendas.sql (excerpt -- full version in patterns/incremental-fact-postgres.md)
{{
    config(
        materialized='incremental',
        unique_key='venda_id',
        incremental_strategy='delete+insert',
        on_schema_change='append_new_columns',
        indexes=[
            {'columns': ['venda_id'], 'unique': True},
            {'columns': ['data_sk']},
        ]
    )
}}

select ...
from {{ ref('int_vendas_enriquecidas') }}
{% if is_incremental() %}
where atualizado_em >= (select max(atualizado_em) from {{ this }})
{% endif %}
```

```yaml
# dbt_project.yml -- defaults per layer, overridable per model
models:
  dw:
    staging:      {+materialized: view}
    intermediate: {+materialized: ephemeral}
    marts:        {+materialized: table}
```

## Quick Reference

| Materialization | Built as | Use for | Trade-off |
|-----------------|----------|---------|-----------|
| `view` | `create view` | Staging, light logic | Recomputed on every query |
| `table` | `create table as` (rebuilt each run, swap via rename) | Marts, dims | Full rebuild cost every run |
| `incremental` | Table + insert/merge of new rows | Large/append-heavy facts | Filter logic, `--full-refresh` on logic change |
| `ephemeral` | CTE inlined in children | Intermediate helpers | Not queryable; harder to debug; no unit-test input except `format: sql` |
| `materialized_view` | `create materialized view` | Postgres-native refresh | `on_configuration_change: apply\|continue\|fail` |

| Incremental strategy (dbt-postgres) | Behavior | Needs |
|-------------------------------------|----------|-------|
| `append` | Insert all selected rows | Default w/o `unique_key`; duplicates possible |
| `delete+insert` | Delete target rows matching `unique_key`, insert new | Default with `unique_key`; any PG version |
| `merge` | `MERGE` update/insert on `unique_key` | Postgres >= 15 (stack runs 18); `incremental_predicates` |
| `microbatch` | Runs time batches by `event_time` | `event_time`, `begin`, `batch_size` (+ upstream `event_time`) |

| Config | Values | Notes |
|--------|--------|-------|
| `on_schema_change` | `ignore` (default), `fail`, `append_new_columns`, `sync_all_columns` | Never backfills old rows |
| `indexes` (Postgres) | `[{columns: [...], unique: bool, type: btree\|hash\|gin...}]` | Tables, incrementals, seeds, snapshots, MVs |
| `unlogged: true` (Postgres) | Unlogged table | Faster, not crash-safe |

## Common Mistakes

### Wrong

```sql
{{ config(materialized='incremental') }}   -- no unique_key, no filter
select * from {{ ref('stg_erp__vendas') }} -- every run appends ALL rows again
```

### Correct

```sql
{{ config(materialized='incremental', unique_key='venda_id') }}
select * from {{ ref('stg_erp__vendas') }}
{% if is_incremental() %}
where atualizado_em >= (select max(atualizado_em) from {{ this }})
{% endif %}
```

Also: `unique_key` columns must never be NULL (rows will duplicate). After changing the
logic of an incremental model run `dbt build -s model+ --full-refresh`.

## Related

- [incremental-fact-postgres](../patterns/incremental-fact-postgres.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [models-ref-dag](../concepts/models-ref-dag.md)
