# Kimball Star Schema Marts

> **Purpose**: Model the marts layer as dimensions + a fact table with hashed surrogate keys, ready for Metabase
> **MCP Validated**: 2026-10-09

## When to Use

- Business process with a clear grain (here: 1 row per sale item) and descriptive entities (customer, product, date)
- BI users slice measures by dimension attributes (Metabase questions/dashboards)
- Following *The Data Warehouse Toolkit* (Kimball) as recommended in the project README

## Implementation

```sql
-- models/marts/core/dim_produtos.sql   (SCD type 1: current state only)
select
    {{ dbt_utils.generate_surrogate_key(['produto_id']) }} as produto_sk,
    produto_id,
    nome_produto,
    categoria,
    preco_lista,
    is_ativo
from {{ ref('stg_erp__produtos') }}
```

```sql
-- models/marts/core/dim_data.sql   (calendar; role-playing for any date column)
with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('" ~ var('data_inicio_calendario') ~ "' as date)",
        end_date="cast('2031-01-01' as date)"
    ) }}

)

select
    cast(to_char(date_day, 'YYYYMMDD') as integer) as data_sk,   -- smart key 20261009
    cast(date_day as date)                         as data,
    extract(year from date_day)::int               as ano,
    extract(quarter from date_day)::int            as trimestre,
    extract(month from date_day)::int              as mes,
    extract(day from date_day)::int                as dia,
    extract(isodow from date_day)::int             as dia_semana_iso,
    extract(isodow from date_day) in (6, 7)        as is_fim_de_semana
from spine
```

```sql
-- models/intermediate/int_vendas_enriquecidas.sql   (ephemeral)
with vendas as (

    select * from {{ ref('stg_erp__vendas') }}

)

select
    venda_id, cliente_id, produto_id, data_venda, quantidade, valor_unitario,
    quantidade * valor_unitario as valor_bruto,
    status, atualizado_em
from vendas
where status <> 'cancelada'
```

```sql
-- models/marts/core/fct_vendas.sql  -- table version (start here; see incremental pattern)
with vendas as (

    select * from {{ ref('int_vendas_enriquecidas') }}

)

select
    venda_id,                                                      -- degenerate dimension
    {{ dbt_utils.generate_surrogate_key(['produto_id']) }} as produto_sk,
    {{ dbt_utils.generate_surrogate_key(['cliente_id']) }} as cliente_sk,   -- SCD1 customer
    cast(to_char(data_venda, 'YYYYMMDD') as integer)     as data_sk,
    quantidade,
    valor_unitario,
    valor_bruto
from vendas
```

```yaml
# models/marts/core/_core__models.yml (excerpt)
models:
  - name: fct_vendas
    description: "Fato de vendas; grao = 1 linha por item de venda"
    columns:
      - name: venda_id
        data_tests: [unique, not_null]
      - name: produto_sk
        data_tests:
          - relationships:
              arguments: {to: ref('dim_produtos'), field: produto_sk}
      - name: data_sk
        data_tests:
          - relationships:
              arguments: {to: ref('dim_data'), field: data_sk}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `packages.yml` | `dbt-labs/dbt_utils` `[">=1.4.0", "<2.0.0"]` | Resolved 1.4.1 with `dbt deps` |
| `generate_surrogate_key([...])` | md5 of `-`-joined, null-safe values | Deterministic: fact computes SKs without joining SCD1 dims |
| `surrogate_key_treat_nulls_as_empty_strings` var | `false` | Legacy `surrogate_key()` null behavior |
| `date_spine` | `end_date` exclusive | Column `date_day`; extend horizon as needed |
| `var('data_inicio_calendario')` | `"2020-01-01"` | Defined in `dbt_project.yml` |
| `+materialized` (marts) | `table` | Facts move to incremental when rebuild gets slow |

## Example Usage

```bash
dbt deps
dbt build -s "+fct_vendas"                 # dims, staging, fact + all tests
dbt build -s marts --exclude dim_data      # rebuild marts, keep calendar
```

```sql
-- Metabase / ad-hoc: revenue by category and month
select p.categoria, d.ano, d.mes, sum(f.valor_bruto) as receita
from marts.fct_vendas f
join marts.dim_produtos p using (produto_sk)
join marts.dim_data d using (data_sk)
group by 1, 2, 3;
```

Design rules: declare the grain first; facts hold FKs + additive measures; dims hold
descriptive attributes; for SCD2 customers replace the hashed `cliente_sk` with the
point-in-time lookup in [snapshot-scd2-dimension](snapshot-scd2-dimension.md). Import
refs in CTEs (`with x as (select * from {{ ref() }})`): `--empty` breaks
`{{ ref() }} as alias` (verified).

## See Also

- [incremental-fact-postgres](../patterns/incremental-fact-postgres.md)
- [snapshot-scd2-dimension](../patterns/snapshot-scd2-dimension.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [materializations](../concepts/materializations.md)
