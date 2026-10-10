# Properties YAML with Tests, Docs and Freshness

> **Purpose**: One properties file per folder that documents models, enforces data quality and wires severity/thresholds
> **MCP Validated**: 2026-10-09

## When to Use

- Every new staging or mart model (minimum: primary key `unique` + `not_null`)
- Foreign keys between facts and dimensions (`relationships`)
- Business rules (allowed statuses, non-negative values, composite uniqueness)

## Implementation

```yaml
# models/staging/erp/_erp__models.yml
models:
  - name: stg_erp__clientes
    description: "Clientes limpos e tipados; 1 linha por cliente"
    columns:
      - name: cliente_id
        description: "Chave natural do ERP"
        data_tests: [unique, not_null]
      - name: uf
        data_tests:
          - accepted_values:
              arguments:
                values: ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                         "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
              config:
                severity: warn                 # bad UF should not stop the pipeline

  - name: stg_erp__produtos
    columns:
      - name: produto_id
        data_tests: [unique, not_null]
      - name: preco_lista
        data_tests:
          - dbt_utils.accepted_range:
              arguments:
                min_value: 0

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
        description: '{{ doc("status_venda") }}'
        data_tests:
          - accepted_values:
              arguments:
                values: ["concluida", "cancelada", "devolvida"]
```

```yaml
# models/marts/core/_core__models.yml (fact part)
models:
  - name: fct_vendas
    description: "Fato de vendas; grao = 1 linha por item de venda"
    columns:
      - name: venda_id
        data_tests: [unique, not_null]
      - name: cliente_sk
        data_tests:
          - not_null:
              config:
                severity: warn                 # sale before any customer version
          - relationships:
              arguments:
                to: ref('dim_clientes')
                field: cliente_sk
      - name: valor_bruto
        data_tests:
          - dbt_utils.expression_is_true:
              arguments:
                expression: ">= 0"
```

```yaml
# dbt_project.yml -- project-wide test defaults
data_tests:
  dw:
    +severity: error          # do NOT set +store_failures: false here: it beats the CLI flag
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| File names | `_<dir>__models.yml`, `_<source>__sources.yml` | One per folder; underscore sorts them first |
| `data_tests:` | - | Key since 1.8 (`tests:` still accepted) |
| `arguments:` | - | Generic test inputs (1.10.5+); `config:` beside it |
| `severity` | `error` | `warn` reports but does not fail `dbt build` |
| `warn_if` / `error_if` | `!=0` | Thresholds, e.g. `error_if: ">100"` |
| `where` | none | Test a subset, e.g. recent partitions |
| `store_failures` | `false` | Persist failing rows; explicit config overrides `--store-failures` (verified) |
| Each model | once per project | Declaring a model in two YAML files is a parse error (verified) |

## Example Usage

```bash
dbt test -s stg_erp__vendas                # tests of one model
dbt test -s "source:erp"                   # tests declared on sources
dbt build -s marts                         # build + test in DAG order
dbt ls -s "test_type:generic" | wc -l      # inventory of generic tests
```

Minimum per model: PK `unique` + `not_null`; for facts, `relationships` to each dimension
and a rule on measures. Verified: the full project (35 data tests + 1 unit test) passed
with `dbt build` on Postgres 16; old top-level test arguments emit
`MissingArgumentsPropertyInGenericTestDeprecation`.

## See Also

- [testing](../concepts/testing.md)
- [documentation](../concepts/documentation.md)
- [sources-freshness](../concepts/sources-freshness.md)
- [staging-model](../patterns/staging-model.md)
