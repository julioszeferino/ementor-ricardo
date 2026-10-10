# Testing: Data Tests and Unit Tests

> **Purpose**: Assert data quality on built tables (data tests) and model logic on fixed inputs (unit tests)
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

**Data tests** are SELECTs that return failing rows; 0 rows = pass. **Generic** tests
(`unique`, `not_null`, `accepted_values`, `relationships`, package tests like
`dbt_utils.expression_is_true`) are declared in YAML under `data_tests:`; **singular**
tests are `.sql` files in `tests/`. **Unit tests** (1.8+) run a model's SQL against
mocked inputs and compare with expected rows *before* the model is built -- use them for
tricky logic (incremental filters, CASE rules), in dev/CI only. Since 1.10.5 generic test
inputs go under `arguments:`; the top-level form raises
`MissingArgumentsPropertyInGenericTestDeprecation` (verified on 1.11.15).

## The Pattern

```yaml
# models/staging/erp/_erp__models.yml (excerpt)
models:
  - name: stg_erp__vendas
    columns:
      - name: venda_id
        data_tests: [unique, not_null]
      - name: cliente_id
        data_tests:
          - not_null
          - relationships:
              arguments:
                to: ref('stg_erp__clientes')
                field: cliente_id
      - name: status
        data_tests:
          - accepted_values:
              arguments:
                values: ["concluida", "cancelada", "devolvida"]
              config:
                severity: warn          # config stays OUTSIDE arguments
                where: "data_venda >= current_date - 30"
```

```sql
-- tests/assert_fct_vendas_sem_vendas_futuras.sql  (singular: returns failing rows)
with fatos as (select * from {{ ref('fct_vendas') }}),
     datas as (select * from {{ ref('dim_data') }})

select fatos.venda_id, datas.data
from fatos
join datas on datas.data_sk = fatos.data_sk
where datas.data > current_date
```

```bash
dbt test -s stg_erp__vendas               # data + unit tests attached to the model
dbt test -s "test_type:unit"              # | test_type:data | :generic | :singular
dbt build --exclude-resource-type unit_test --target prod   # skip unit tests in prod
dbt test --store-failures -s fct_vendas   # failing rows -> table per test (dev: target schema)
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `accepted_values` with ints | Needs `quote: false` in `arguments` | Default single-quotes values |
| `relationships` | Ignores NULL FKs | Add `not_null` if NULL is invalid |
| `config: {severity: warn}` | Warn, do not fail | Also `error_if` / `warn_if: ">10"` |
| `config: {where: "..."}` | Test a subset | Not inside `arguments` |
| `+store_failures: true` | Audit tables of failures | Schema `dbt_test__audit` via generate_schema_name; explicit config beats the CLI flag |
| Unit test `input: this` | Mock current table of an incremental | With `overrides.macros.is_incremental: true` |
| Unit test on model with ephemeral parent | Input needs `format: sql` | Verified with `dbt build` |
| `DBT_ENGINE_EXCLUDE_RESOURCE_TYPES=unit_test` | Same as the flag (1.11) | Env var for prod jobs |
| `dbt build` | Runs each node, then its tests; skips children on failure | Preferred over run + test |

## Common Mistakes

### Wrong

```yaml
data_tests:
  - accepted_values:
      values: [1, 2, 3]       # top-level args: deprecated in 1.10.5+
      severity: warn          # mixed with config
```

### Correct

```yaml
data_tests:
  - accepted_values:
      arguments:
        values: [1, 2, 3]
        quote: false
      config:
        severity: warn
```

Unit tests must live in YAML under `models/` (not `tests/`) and every `ref`/`source`
used by the model must be listed as an `input`.

## Related

- [schema-yml-tests](../patterns/schema-yml-tests.md)
- [incremental-fact-postgres](../patterns/incremental-fact-postgres.md)
- [testing-pytest (python KB)](../../python/patterns/testing-pytest.md)
