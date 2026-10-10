# Staging Model from a Source

> **Purpose**: Turn one raw ingestion table into a clean, typed, consistently named view that every downstream model builds on
> **MCP Validated**: 2026-10-09

## When to Use

- Every raw table loaded by the Python ingestion into schema `raw` (1 source table -> 1 staging model)
- Raw columns arrive as text / inconsistent names / cents instead of currency
- You want one place to fix data-entry noise (blank strings, casing, whitespace)

## Implementation

```yaml
# models/staging/erp/_erp__sources.yml
sources:
  - name: erp
    description: "Arquivos de data/ carregados pela ingestao Python no schema raw"
    database: warehouse
    schema: raw
    config:
      loaded_at_field: _loaded_at
      freshness:
        warn_after: {count: 24, period: hour}
        error_after: {count: 48, period: hour}
    tables:
      - name: clientes
      - name: produtos
      - name: vendas
        config:
          freshness:
            warn_after: {count: 6, period: hour}
            error_after: {count: 24, period: hour}
```

```sql
-- macros/centavos_para_reais.sql  /  macros/limpar_texto.sql
{% macro centavos_para_reais(coluna, casas=2) -%}
    round(({{ coluna }})::numeric / 100, {{ casas }})
{%- endmacro %}

{% macro limpar_texto(coluna) -%}
    nullif(trim({{ coluna }}), '')
{%- endmacro %}
```

```sql
-- models/staging/erp/stg_erp__vendas.sql
with

source as (

    select * from {{ source('erp', 'vendas') }}

),

renamed as (

    select
        ---------- ids
        cast(id as integer)                                  as venda_id,
        cast(id_cliente as integer)                          as cliente_id,
        cast(id_produto as integer)                          as produto_id,

        ---------- dates
        cast(data_venda as date)                             as data_venda,

        ---------- measures
        cast(quantidade as integer)                          as quantidade,
        {{ centavos_para_reais('valor_unitario_centavos') }} as valor_unitario,

        ---------- categories
        lower(trim(status))                                  as status,

        ---------- metadata
        cast(atualizado_em as timestamp)                     as atualizado_em,
        _loaded_at

    from source

)

select * from renamed
```

```sql
-- models/staging/erp/stg_erp__clientes.sql (renamed CTE only; same skeleton)
        cast(id as integer)                      as cliente_id,
        {{ limpar_texto('nome') }}               as nome_cliente,
        lower({{ limpar_texto('email') }})       as email,
        upper(trim(uf))                          as uf,
        {{ limpar_texto('cidade') }}             as cidade,
        cast(data_cadastro as date)              as data_cadastro,
        cast(atualizado_em as timestamp)         as atualizado_em,
        _loaded_at
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `+materialized` (staging folder) | `view` | Always-fresh, no storage; switch to table only if very slow |
| `+schema` | `staging` | Lands in `staging` in prod, `target.schema` in dev |
| File name | `stg_[source]__[entity]s.sql` | Double underscore separates source and entity |
| Column naming | `<entity>_id`, `is_`/`has_` booleans, `data_`/`_em` dates | Consistent across all staging models |
| Raw table columns | assumed: `id`, text fields, `atualizado_em`, `_loaded_at` | Adjust to the real ingestion schema |

## Example Usage

```bash
dbt build -s stg_erp__vendas          # build view + run its tests
dbt build -s "source:erp+"            # everything downstream of the source
dbt show -s stg_erp__vendas --limit 5 # preview (needs DB)
```

Allowed here: renaming, casting, simple math (cents -> reais), CASE categorization,
cleaning. Not here: joins and aggregations (they belong in intermediate/marts).
Verified: these models built as views on Postgres 16 with `dbt build` (raw columns
as text, cast in staging).

## See Also

- [sources-freshness](../concepts/sources-freshness.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [jinja-macros](../concepts/jinja-macros.md)
- [schema-yml-tests](../patterns/schema-yml-tests.md)
- [streaming-etl-pipeline (python KB)](../../python/patterns/streaming-etl-pipeline.md)
