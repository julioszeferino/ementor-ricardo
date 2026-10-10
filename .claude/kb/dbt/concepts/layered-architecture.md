# Layered Architecture: staging -> intermediate -> marts

> **Purpose**: Organize models in layers with naming conventions and land each layer in its own Postgres schema
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

dbt's structure guide uses three layers. **Staging**: 1:1 with source tables, only
renaming, casting, light cleaning; materialized as views; the only place `source()` is
used. **Intermediate**: purpose-built joins, re-graining, isolating complex logic;
ephemeral or views in a separate schema. **Marts**: business-facing entities as tables
(or incremental). For this project the marts are a **Kimball star schema** (`dim_*`,
`fct_*`); dbt's guide prefers wide denormalized marts, which you can add on top for
Metabase. A `generate_schema_name` override makes each layer land in its exact schema
in prod (`staging`, `marts`, created by the Postgres init script) instead of
`<target_schema>_<custom>`.

## The Pattern

```text
models/
├── staging/erp/                         # subfolder per SOURCE system
│   ├── _erp__sources.yml
│   ├── _erp__models.yml
│   └── stg_erp__clientes.sql            # stg_[source]__[entity]s
├── intermediate/                        # subfolder per business area once it grows
│   └── int_vendas_enriquecidas.sql      # int_[entity]s_[verb]s
└── marts/core/                          # subfolder per business area / domain
    ├── _core__models.yml
    ├── dim_clientes.sql  dim_produtos.sql  dim_data.sql
    └── fct_vendas.sql
```

```sql
-- macros/generate_schema_name.sql
{#- prod: custom schema as-is (staging, marts...); dev/ci: everything in target.schema -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ generate_schema_name_for_env(custom_schema_name, node) }}
{%- endmacro %}
```

Resolved schemas (verified from `manifest.json` after `dbt parse --target dev|prod`):

| Node | `--target dev` (schema `dbt_dev`) | `--target prod` |
|------|-----------------------------------|-----------------|
| `stg_erp__*` (view) | `dbt_dev` | `staging` |
| `int_vendas_enriquecidas` (ephemeral) | not created | not created |
| `dim_*`, `fct_vendas` | `dbt_dev` | `marts` |
| `snap_erp__clientes` | `dbt_dev` | `snapshots` |
| seed `uf_regioes` | `dbt_dev` | `staging` |

## Quick Reference

| Layer | Prefix | Materialization | Allowed | Avoid |
|-------|--------|-----------------|---------|-------|
| Staging | `stg_[source]__[entity]s` | view | rename, cast, basic math, categorize | joins, aggregations |
| Intermediate | `int_[entity]s_[verb]s` | ephemeral / view | joins, pivots, re-grain | exposing to BI |
| Marts (dims) | `dim_[entity]` | table | surrogate keys, attributes, SCD | metrics |
| Marts (facts) | `fct_[process]` | table -> incremental | measures + FK surrogate keys at a declared grain | mixing grains |
| Snapshots | `snap_[source]__[entity]` | snapshot | SCD2 history of mutable sources | business logic |

## Common Mistakes

### Wrong

```sql
-- marts model reading raw data directly and joining 6 sources in one file
select ... from {{ source('erp', 'vendas') }} v join {{ source('erp', 'clientes') }} c ...
```

### Correct

```sql
-- marts read staging/intermediate only; source() lives in staging
select ... from {{ ref('int_vendas_enriquecidas') }} v
```

Do not replace the macro body with just `{{ custom_schema_name }}` for all targets: dev
and CI runs would overwrite prod schemas. `generate_schema_name_for_env` only applies
custom schemas when `target.name == 'prod'`, so the prod output must be named `prod`.

## Related

- [materializations](../concepts/materializations.md)
- [staging-model](../patterns/staging-model.md)
- [star-schema-marts](../patterns/star-schema-marts.md)
- [postgres-service (docker KB)](../../docker/patterns/postgres-service.md)
