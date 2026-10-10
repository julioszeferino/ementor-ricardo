# Documentation and Lineage

> **Purpose**: Describe models/columns in YAML, reuse long texts with doc blocks, generate the docs site and persist comments to Postgres
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

Every resource and column can have a `description:` in its properties YAML. Long or
shared text goes in `{% docs name %}` blocks inside any `.md` file under a resource path,
referenced with `{{ doc('name') }}`. `dbt docs generate` writes `manifest.json` (project
graph) and `catalog.json` (columns/types queried from the database) to `target/`;
`dbt docs serve` hosts the site with the lineage graph. `persist_docs` writes the same
descriptions as `COMMENT ON` in Postgres, so Metabase and SQL clients see them.

## The Pattern

```markdown
<!-- models/staging/erp/docs.md -->
{% docs status_venda %}
Status da venda no ERP:

| status     | significado                    |
|------------|--------------------------------|
| concluida  | venda faturada                 |
| cancelada  | cancelada antes do faturamento |
| devolvida  | faturada e depois devolvida    |
{% enddocs %}
```

```yaml
# models/staging/erp/_erp__models.yml (excerpt)
models:
  - name: stg_erp__vendas
    description: "Itens de venda limpos e tipados; 1 linha por item"
    columns:
      - name: status
        description: '{{ doc("status_venda") }}'
```

```yaml
# dbt_project.yml -- push descriptions to the database as comments
models:
  dw:
    +persist_docs: {relation: true, columns: true}
```

```bash
dbt docs generate                  # needs a DB connection (catalog queries)
dbt docs serve --port 8081         # 8080 is taken by Airflow in this stack
dbt docs generate --static         # single self-contained target/static_index.html
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `description:` on model/column | Shown in docs site | Markdown allowed |
| `'{{ doc("x") }}'` | Text of docs block `x` | Quote the Jinja in YAML |
| `persist_docs.relation` | `COMMENT ON TABLE/VIEW` | Verified on Postgres views and tables |
| `persist_docs.columns` | `COMMENT ON COLUMN` | Column must be listed in YAML |
| `config: {docs: {show: false}}` | Hidden from docs site | e.g. helper models |
| `exposures:` in YAML | Downstream consumer node (e.g. Metabase dashboard) | `dbt ls -s +exposure:name` |
| `config: {meta: {owner: "time-dados"}}` | Custom metadata | Custom keys belong in `meta` (1.10+) |
| `{% docs __overview__ %}` | Replaces docs site home page | Project-level overview |

## Common Mistakes

### Wrong

```yaml
columns:
  - name: status
    description: {{ doc("status_venda") }}   # unquoted Jinja -> YAML parse error
    owner: time-dados                         # custom key outside meta
```

### Correct

```yaml
columns:
  - name: status
    description: '{{ doc("status_venda") }}'
    config:
      meta: {owner: time-dados}
```

The docs site is static: regenerate after each deploy (e.g. an Airflow task after
`dbt build`). Never publish `target/` with prod credentials in logs.

## Related

- [schema-yml-tests](../patterns/schema-yml-tests.md)
- [project-structure](../concepts/project-structure.md)
- [testing](../concepts/testing.md)
