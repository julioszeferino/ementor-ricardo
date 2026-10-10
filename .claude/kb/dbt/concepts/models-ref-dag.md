# Models, ref/source and the DAG

> **Purpose**: Write models as SELECTs, wire them with ref()/source(), and select parts of the DAG
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A **model** is one `.sql` file containing one `SELECT`; dbt wraps it in the DDL for its
materialization. `{{ ref('model') }}` and `{{ source('src', 'table') }}` resolve to the
right relation for the current target **and** declare a dependency, so dbt builds a
DAG and runs nodes in order (parallel up to `threads`). The file name is the model
name, so names must be unique across the project.

## The Pattern

```sql
-- models/marts/core/dim_produtos.sql
-- SCD type 1: current state only, 1 row per product
select
    {{ dbt_utils.generate_surrogate_key(['produto_id']) }} as produto_sk,
    produto_id,
    nome_produto,
    categoria,
    preco_lista,
    is_ativo
from {{ ref('stg_erp__produtos') }}
```

```text
source:erp.produtos -> stg_erp__produtos -> dim_produtos
source:erp.vendas   -> stg_erp__vendas   -> int_vendas_enriquecidas -> fct_vendas
source:erp.clientes -> snap_erp__clientes -> dim_clientes ----------^
```

```bash
dbt ls -s "+fct_vendas"                    # everything fct_vendas depends on
dbt build -s "stg_erp__vendas+"            # model + all descendants (+ their tests)
dbt build -s "1+fct_vendas"                # one level of parents
dbt build -s "@stg_erp__vendas"            # descendants AND their ancestors
dbt run -s "path:models/marts" --exclude "fct_vendas"
dbt build -s "tag:diario,config.materialized:incremental"   # comma = intersection
dbt build -s "staging marts"               # space = union
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `ref('stg_erp__vendas')` (dev) | `"warehouse"."dbt_dev"."stg_erp__vendas"` | Schema from generate_schema_name |
| `ref('stg_erp__vendas')` (prod) | `"warehouse"."staging"."stg_erp__vendas"` | Same code, other target |
| `ref('dbt_utils', 'x')` | Model in a package | Two-arg form |
| `{{ this }}` | Relation of the current model | Used in incremental filters |
| `-s model+` / `+model` / `n+model` / `@model` | Descendants / ancestors / n levels / both | Graph operators |
| `-s "resource_type:snapshot"` | Select by type (1.11) | Also `--resource-type` on `ls` |
| `--models` / `-m` | Deprecated (warns in 1.10+) | Use `--select` / `-s` |
| `dbt compile -s m` | SQL in `target/compiled/` | Debug Jinja output |
| `dbt show -s m --limit 10` | Preview rows | Needs DB connection |

## Common Mistakes

### Wrong

```sql
-- hardcoded schema: no dependency edge, wrong schema in dev, may run before upstream
select * from staging.stg_erp__produtos
```

### Correct

```sql
select * from {{ ref('stg_erp__produtos') }}
```

Other mistakes: two models with the same file name in different folders (parse error);
a trailing `;` in a model (can break the wrapping DDL); `select *` in marts (columns
change silently -- list them).

## Related

- [sources-freshness](../concepts/sources-freshness.md)
- [materializations](../concepts/materializations.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [project-setup-commands](../patterns/project-setup-commands.md)
