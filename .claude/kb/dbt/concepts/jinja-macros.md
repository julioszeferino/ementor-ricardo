# Jinja and Macros

> **Purpose**: Reuse SQL logic and add control flow with Jinja, macros, vars and target context
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

Every model/test/YAML value is a Jinja template rendered at compile time into plain SQL.
`{{ ... }}` prints an expression, `{% ... %}` runs a statement (`if`, `for`, `set`),
`{# ... #}` is a comment, and `{%- -%}` trims whitespace. **Macros** (`macros/*.sql`)
are reusable Jinja functions -- your own or from packages (`dbt_utils.*`), plus dbt's
cross-database helpers (`dbt.date_trunc`, `dbt.dateadd`...). Keep macros small: if
reading the model needs `dbt compile`, the abstraction went too far.

## The Pattern

```sql
-- macros/centavos_para_reais.sql
{% macro centavos_para_reais(coluna, casas=2) -%}
    round(({{ coluna }})::numeric / 100, {{ casas }})
{%- endmacro %}

-- macros/limpar_texto.sql
{#- trim + collapse blanks to null; usable in any model -#}
{% macro limpar_texto(coluna) -%}
    nullif(trim({{ coluna }}), '')
{%- endmacro %}
```

```sql
-- usage inside a model
select
    {{ limpar_texto('descricao') }}             as nome_produto,
    {{ centavos_para_reais('preco_centavos') }} as preco_lista,
    {%- for s in ['concluida', 'cancelada', 'devolvida'] %}
    sum(case when status = '{{ s }}' then 1 else 0 end) as qtd_{{ s }}
    {{- "," if not loop.last }}
    {%- endfor %}
from {{ ref('stg_erp__vendas') }}
{% if target.name != 'prod' %}
where data_venda >= current_date - 90          -- smaller dev builds
{% endif %}
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `{{ var('lookback_dias', 3) }}` | Project var or default | `--vars '{lookback_dias: 7}'` overrides |
| `{{ env_var('X', 'd') }}` | Env value (string) | Prefer in profiles; avoid in models |
| `{{ target.name }}` / `target.schema` | `dev` / `dbt_dev` | Env-specific logic |
| `{{ this }}` | Current model relation | Incremental filters, hooks |
| `{{ dbt.date_trunc('day', 'col') }}` | Adapter-correct SQL | Cross-db helpers in `dbt` namespace |
| `{{ dbt_utils.star(ref('m'), except=['_loaded_at']) }}` | Column list | Needs DB at compile time |
| `{% set cols = [...] %}` | Jinja variable | Lists, dicts, strings |
| `{{ log('msg', info=true) }}` | Prints during run | Debugging |
| `dbt run-operation macro --args '{a: 1}'` | Executes a macro | Admin tasks (grants, cleanup) |
| `{% macro generate_schema_name(...) %}` in project | Overrides built-in | Package versions of it are ignored |
| `config.meta_get('owner')` | Custom meta value | 1.10+; custom keys belong in `meta` |

## Common Mistakes

### Wrong

```sql
-- Jinja nested inside Jinja, and a macro call without braces
select {{ centavos_para_reais('{{ var("col") }}') }}, limpar_texto('nome') from ...
```

### Correct

```sql
select {{ centavos_para_reais(var('col')) }}, {{ limpar_texto('nome') }} from ...
```

Inside `{{ }}`/`{% %}` you are already in Jinja: reference variables and functions
directly; string concatenation uses `~` (e.g. `"cast('" ~ var('d') ~ "' as date)"`).

## Related

- [models-ref-dag](../concepts/models-ref-dag.md)
- [layered-architecture](../concepts/layered-architecture.md)
- [staging-model](../patterns/staging-model.md)
