# Incremental Fact Model on Postgres

> **Purpose**: Load only new/changed rows into a large fact table with delete+insert, a lookback window, Postgres indexes and a unit test
> **MCP Validated**: 2026-10-09

## When to Use

- The table version of `fct_vendas` takes too long to rebuild every run
- Source rows have a reliable change timestamp (`atualizado_em`) and a unique key (`venda_id`)
- Late-arriving updates (e.g. quantity corrected a day later) must overwrite the old row

## Implementation

```sql
-- models/marts/core/fct_vendas.sql
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

with vendas as (

    select * from {{ ref('int_vendas_enriquecidas') }}

    {% if is_incremental() %}
    -- reprocess a lookback window to catch late-arriving updates
    where atualizado_em >= (
        select coalesce(max(atualizado_em), cast('1900-01-01' as timestamp))
               - interval '{{ var("lookback_dias", 3) }} days'
        from {{ this }}
    )
    {% endif %}

),

clientes as (

    select cliente_sk, cliente_id, valido_de, valido_ate
    from {{ ref('dim_clientes') }}

)

select
    v.venda_id,                                                       -- degenerate dim
    {{ dbt_utils.generate_surrogate_key(['v.produto_id']) }} as produto_sk,
    c.cliente_sk,                                                     -- version valid on sale date
    cast(to_char(v.data_venda, 'YYYYMMDD') as integer)     as data_sk,
    v.quantidade,
    v.valor_unitario,
    v.valor_bruto,
    v.status,
    v.atualizado_em
from vendas as v
left join clientes as c
    on  v.cliente_id = c.cliente_id
    and v.data_venda >= c.valido_de
    and v.data_venda <  c.valido_ate
```

```yaml
# models/marts/core/_core__models.yml -- unit test of the incremental branch
unit_tests:
  - name: test_fct_vendas_incremental_traz_apenas_novas
    model: fct_vendas
    overrides:
      macros:
        is_incremental: true
      vars:
        lookback_dias: 0
    given:
      - input: ref('int_vendas_enriquecidas')   # ephemeral parent -> format: sql
        format: sql
        rows: |
          select 1 as venda_id, 10 as cliente_id, 100 as produto_id, date '2026-10-01' as data_venda,
                 2 as quantidade, 5.00 as valor_unitario, 10.00 as valor_bruto, 'concluida' as status,
                 timestamp '2026-10-01 10:00' as atualizado_em
          union all
          select 2, 10, 100, date '2026-10-02', 1, 5.00, 5.00, 'concluida', timestamp '2026-10-02 10:00'
      - input: ref('dim_clientes')
        rows:
          - {cliente_sk: "a", cliente_id: 10, valido_de: "1900-01-01", valido_ate: "9999-12-31"}
      - input: this                              # current contents of fct_vendas
        rows:
          - {venda_id: 1, atualizado_em: "2026-10-01 10:00:00"}
    expect:                     # rows to delete+insert: >= re-selects the last timestamp
      rows:
        - {venda_id: 1, cliente_sk: "a", data_sk: 20261001}
        - {venda_id: 2, cliente_sk: "a", data_sk: 20261002}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `incremental_strategy` | `delete+insert` (with `unique_key`) | `merge` also works (Postgres 15+; verified `MERGE` on PG 16) |
| `unique_key` | none | Must be NOT NULL and unique, else duplicates |
| `var('lookback_dias')` | `3` | Window re-read each run; idempotent thanks to `unique_key` |
| `on_schema_change` | `ignore` | `append_new_columns` adds new columns; never backfills |
| `indexes` | none | Created after build; unique index guards the grain |
| `incremental_predicates` | none | Limit the scan of the target during merge/delete |
| `--full-refresh` | off | Rebuild from scratch after logic changes (also downstream with `+`) |

## Example Usage

```bash
dbt build -s fct_vendas                              # incremental run (INSERT 0 n)
dbt build -s fct_vendas --vars '{lookback_dias: 30}' # wider reprocessing window
dbt build -s fct_vendas+ --full-refresh              # after changing the SELECT
# fresh database / CI: the unit test's `input: this` needs the relation to exist
dbt build --empty --exclude-resource-type unit_test && dbt build
```

Verified on Postgres 16 (scratch run): first build created the table; after updating
a source row and inserting a new sale, the next run replaced the updated row and added
the new one; the SCD2 join picked the customer version valid on each sale date.
Without the `--empty` pre-step the unit test errors with "relation doesn't exist";
`dbt run --empty` alone is not enough on a fresh DB (snapshots are not part of `run`).
Alternative for very large append-only data: `incremental_strategy='microbatch'` with
`event_time`, `begin` and `batch_size` (supported by dbt-postgres).

## See Also

- [materializations](../concepts/materializations.md)
- [star-schema-marts](../patterns/star-schema-marts.md)
- [snapshot-scd2-dimension](../patterns/snapshot-scd2-dimension.md)
- [testing](../concepts/testing.md)
