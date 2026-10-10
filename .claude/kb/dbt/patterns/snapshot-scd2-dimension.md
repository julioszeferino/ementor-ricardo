# Snapshot-Backed SCD Type 2 Dimension

> **Purpose**: Keep full history of customer attributes and let facts point to the version valid at the event date
> **MCP Validated**: 2026-10-09

## When to Use

- Source table is overwritten in place (the ingestion reloads `raw.clientes` each run)
- Analysts must report sales by the customer's region *at the time of the sale*
- You need an auditable "as of" view of a mutable entity

## Implementation

```yaml
# snapshots/snap_erp__clientes.yml
snapshots:
  - name: snap_erp__clientes
    relation: source('erp', 'clientes')
    description: "Historico SCD2 do cadastro de clientes"
    config:
      unique_key: id
      strategy: timestamp
      updated_at: atualizado_em        # must be a real timestamp column in raw
      dbt_valid_to_current: "cast('9999-12-31' as timestamp)"
      hard_deletes: invalidate
```

```sql
-- models/marts/core/dim_clientes.sql
-- SCD type 2: one row per customer VERSION, built from the snapshot
with versoes as (

    select
        *,
        row_number() over (partition by id order by dbt_valid_from) as n_versao
    from {{ ref('snap_erp__clientes') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['id', 'dbt_valid_from']) }} as cliente_sk,
    cast(id as integer)                            as cliente_id,
    nullif(trim(nome), '')                         as nome_cliente,
    upper(trim(uf))                                as uf,
    nullif(trim(cidade), '')                       as cidade,
    -- first version open since "forever" so older facts still find a match
    case when n_versao = 1 then cast('1900-01-01' as timestamp)
         else dbt_valid_from end                   as valido_de,
    dbt_valid_to                                   as valido_ate,
    dbt_valid_to = cast('9999-12-31' as timestamp) as is_atual
from versoes
```

```sql
-- point-in-time lookup inside fct_vendas (see incremental-fact-postgres)
left join clientes as c
    on  v.cliente_id = c.cliente_id
    and v.data_venda >= c.valido_de
    and v.data_venda <  c.valido_ate
```

```yaml
# models/marts/core/_core__models.yml (excerpt)
models:
  - name: dim_clientes
    columns:
      - name: cliente_sk
        data_tests: [unique, not_null]
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          arguments:
            combination_of_columns: [cliente_id, valido_de]
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `strategy` | `timestamp` | `check` + explicit `check_cols` if no trustworthy timestamp |
| `dbt_valid_to_current` | `NULL` | Sentinel date makes `between`-style range joins simple |
| `hard_deletes` | `ignore` | `invalidate` closes the version; `new_record` adds `dbt_is_deleted` row |
| `schema` (from `dbt_project.yml`) | `snapshots` | Prod schema `snapshots`; dev uses `target.schema` |
| SK | `hash(id, dbt_valid_from)` | Stable per version; `dbt_valid_from` never changes |
| `valido_de` of 1st version | `1900-01-01` | Facts older than the first snapshot still join |

## Example Usage

```bash
dbt snapshot                       # capture changes (Airflow: before models)
dbt build -s "snap_erp__clientes+" # snapshot, dim, fact and tests in DAG order
```

Verified scratch run (Postgres 16): customer 10 changed `uf` SP -> RJ on 2025-03-01;
after `dbt build`, `dim_clientes` had 2 versions (SP 1900-01-01..2025-03-01, RJ
2025-03-01..9999-12-31) and a January sale resolved to SP, a March sale to RJ.
Deleting customer 11 from raw set its `dbt_valid_to` to the snapshot time.

| cliente_id | uf | valido_de | valido_ate | is_atual |
|------------|----|-----------|------------|----------|
| 10 | SP | 1900-01-01 | 2025-03-01 | false |
| 10 | RJ | 2025-03-01 | 9999-12-31 | true |

Snapshot tables are history: never drop them (no `--full-refresh` rebuild exists);
include the `snapshots` schema in database backups. Cleaning in `dim_clientes` (not in
the snapshot) keeps raw history intact when cleaning rules change.

## See Also

- [seeds-snapshots](../concepts/seeds-snapshots.md)
- [incremental-fact-postgres](../patterns/incremental-fact-postgres.md)
- [star-schema-marts](../patterns/star-schema-marts.md)
