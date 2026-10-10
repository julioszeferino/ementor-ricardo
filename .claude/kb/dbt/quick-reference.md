# dbt Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-10-09

## Pinned Versions (checked 2026-10-09)

| Component | Reference | Notes |
|-----------|-----------|-------|
| dbt-core | `~=1.11.0` (1.11.15) | 1.12.5 exists; stay on 1.11 with the docker KB |
| dbt-postgres | `~=1.11.0` (1.11.0) | Versioned independently of core |
| dbt_utils | `[">=1.4.0", "<2.0.0"]` (1.4.1) | Supports dbt `>=1.3.0, <3.0.0` |
| Python | 3.12 | dbt-core requires `>=3.10` |
| Postgres | 18 (docker KB) | `merge` needs >= 15 |

## Commands

| Task | Command |
|------|---------|
| Install packages | `dbt deps` |
| Check profile + connection | `dbt debug` |
| Validate project without DB | `dbt parse` |
| Build all (seed, snapshot, run, test) | `dbt build` |
| Build one model + descendants | `dbt build -s stg_erp__vendas+` |
| Model + ancestors | `dbt build -s +fct_vendas` |
| Rebuild incremental from scratch | `dbt build -s fct_vendas+ --full-refresh` |
| Only unit / data tests | `dbt test -s test_type:unit` / `test_type:data` |
| Prod without unit tests | `dbt build --target prod --exclude-resource-type unit_test` |
| Source freshness | `dbt source freshness` |
| Schema-only build | `dbt run -s m --empty` |
| Changed since prod | `dbt build -s state:modified+ --defer --state state/` |
| Retry failures | `dbt retry` |
| Preview / compiled SQL | `dbt show -s m --limit 10` / `dbt compile -s m` |
| Docs | `dbt docs generate && dbt docs serve --port 8081` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Clean one raw table | Staging view `stg_erp__<entity>s` |
| Reusable join/re-grain not for BI | Intermediate, ephemeral (or view) |
| BI-facing entity | Mart table `dim_*` / `fct_*` |
| Fact rebuild too slow | Incremental `delete+insert` + `unique_key` |
| Upsert with predicates on PG >= 15 | `merge` |
| Track attribute history | Snapshot (timestamp) + SCD2 dim |
| Small static mapping | Seed CSV |
| Raw business data | Python ingestion -> source, never a seed |
| Reused SQL expression | Macro |
| Tricky logic | Unit test (dev/CI) |
| Env-specific schemas | `generate_schema_name_for_env` override |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `from raw.vendas` / `from staging.x` | `{{ source('erp','vendas') }}` / `{{ ref('x') }}` |
| `{{ ref('x') }} as v` (breaks `--empty`) | `with x as (select * from {{ ref('x') }})` |
| Generic test args at top level | Nest under `arguments:` (1.10.5+) |
| `freshness:` at source top level | Under `config:` with `loaded_at_field` |
| Password in `profiles.yml` | `"{{ env_var('DBT_PASSWORD') }}"` |
| `port: {{ env_var('P') }}` | `port: "{{ env_var('P', '5432') \| as_number }}"` |
| `localhost` inside containers | Service name `postgres`, port 5432 |
| Incremental without filter/key | `is_incremental()` filter + `unique_key` |
| Custom schema used verbatim in dev | `generate_schema_name_for_env` (custom only when `target.name == 'prod'`) |
| Incremental unit test on fresh DB | `dbt build --empty --exclude-resource-type unit_test` first |
| Dropping snapshot tables | Back them up; history cannot be rebuilt |
| `--models` / `-m` | `--select` / `-s` |

## Related Documentation

| Topic | Path |
|-------|------|
| Getting Started | `concepts/project-structure.md` |
| Run/CI commands | `patterns/project-setup-commands.md` |
| Config rules | `specs/dbt-project.yaml` |
| dbt container | `../docker/patterns/dbt-runner-container.md` |
| Full Index | `index.md` |
