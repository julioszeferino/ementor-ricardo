# Seeds and Snapshots

> **Purpose**: Version small static lookups as CSV (seeds) and capture history of mutable source rows (snapshots, SCD type 2)
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

**Seeds** are CSV files in `seeds/` loaded by `dbt seed` (or `dbt build`) into a table;
use them for small, rarely changing reference data owned by the team (UF -> region,
status mappings) -- never for raw business data, which the Python ingestion loads.
**Snapshots** record changes to rows over time: each run compares the source with the
snapshot table and closes old versions (`dbt_valid_to`) / inserts new ones. Since 1.9
they are configured in YAML with `relation:`; no `target_schema` needed (env-aware via
`generate_schema_name`). Snapshots are the raw history behind SCD2 dimensions.

## The Pattern

```csv
uf,nome_uf,regiao
SP,Sao Paulo,Sudeste
RJ,Rio de Janeiro,Sudeste
```

```yaml
# seeds/_seeds.yml
seeds:
  - name: uf_regioes
    config:
      column_types: {uf: char(2), nome_uf: text, regiao: text}
    columns:
      - name: uf
        data_tests: [unique, not_null]
```

```yaml
# snapshots/snap_erp__clientes.yml
snapshots:
  - name: snap_erp__clientes
    relation: source('erp', 'clientes')       # or ref('some_model')
    config:
      unique_key: id
      strategy: timestamp                     # recommended when a reliable updated_at exists
      updated_at: atualizado_em
      dbt_valid_to_current: "cast('9999-12-31' as timestamp)"   # instead of NULL
      hard_deletes: invalidate                # ignore (default) | invalidate | new_record
```

```bash
dbt seed -s uf_regioes --full-refresh        # recreate after changing columns
dbt snapshot                                 # or as part of: dbt build
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `ref('uf_regioes')` | Seed table | Seeds are refable like models |
| Edit seed rows | Truncate + reload on next `dbt seed` | Column changes need `--full-refresh` |
| `strategy: check` + `check_cols: [uf, cidade]` | Change = any listed column differs | When no trustworthy `updated_at` |
| Snapshot meta columns | `dbt_scd_id`, `dbt_updated_at`, `dbt_valid_from`, `dbt_valid_to` | `dbt_is_deleted` only with `new_record` |
| `dbt_valid_from` (timestamp strategy) | Source `updated_at` of that version | Verified: 1st version = 2024-01-10 08:00 |
| `hard_deletes: invalidate` | Deleted source row gets `dbt_valid_to = snapshot time` | Verified on Postgres 16 |
| `snapshot_meta_column_names: {dbt_valid_from: inicio}` | Renamed meta columns | Optional |
| Snapshot table | Never rebuilt by `--full-refresh` | History lost if you drop it -- back it up |

## Common Mistakes

### Wrong

```yaml
snapshots:
  - name: snap_clientes
    relation: ref('dim_clientes')      # snapshotting a derived mart: logic changes rewrite "history"
    config:
      unique_key: id
      strategy: check
      check_cols: all                  # noisy: any column (even _loaded_at) creates a version
```

### Correct

```yaml
snapshots:
  - name: snap_erp__clientes
    relation: source('erp', 'clientes')
    config: {unique_key: id, strategy: timestamp, updated_at: atualizado_em}
```

Run snapshots on a schedule (Airflow): changes that happen and revert between runs are
never captured. `unique_key` must be truly unique in the source.

## Related

- [snapshot-scd2-dimension](../patterns/snapshot-scd2-dimension.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [sources-freshness](../concepts/sources-freshness.md)
