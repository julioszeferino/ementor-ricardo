# Project Setup, Packages and Run/CI Commands

> **Purpose**: Bootstrap the `dbt/` project with pinned versions and dbt_utils, then run it consistently locally, in Airflow and in CI
> **MCP Validated**: 2026-10-09

## When to Use

- Creating the `dbt/` folder of this repo for the first time
- Adding packages (dbt_utils) or upgrading dbt
- Writing the Airflow task / CI job that runs dbt

## Implementation

```bash
# local (no Docker): Python 3.12 venv with the same pins as the docker KB
python3.12 -m venv .venv-dbt && . .venv-dbt/bin/activate
pip install "dbt-core~=1.11.0" "dbt-postgres~=1.11.0"   # resolved 1.11.15 + 1.11.0
dbt --version
```

```yaml
# dbt/packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.4.0", "<2.0.0"]      # `dbt deps` -> 1.4.1, recorded in package-lock.yml
```

```text
# dbt/.gitignore
target/
logs/
dbt_packages/
state/
.user.yml
```

```sql
-- dbt/macros/generate_schema_name.sql (prod: exact custom schemas; dev: target.schema)
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ generate_schema_name_for_env(custom_schema_name, node) }}
{%- endmacro %}
```

```bash
cd dbt
export DBT_USER=dw DBT_PASSWORD=...      # profiles.yml reads env vars (concepts/profiles-targets.md)
dbt deps                                 # install packages (commit package-lock.yml)
dbt debug                                # profile + connection check
dbt parse                                # no DB needed: validates project, YAML, Jinja refs
dbt build                                # seeds, snapshots, models, tests in DAG order (dev)
dbt build --target prod --exclude-resource-type unit_test
dbt source freshness                     # before build in the scheduled pipeline
dbt docs generate && dbt docs serve --port 8081
```

```yaml
# .github/workflows/ci.yml (job excerpt) -- parse always; build against a throwaway Postgres
dbt:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:18
      env: {POSTGRES_USER: dw, POSTGRES_PASSWORD: dw, POSTGRES_DB: warehouse}
      ports: ["5433:5432"]
      options: >-
        --health-cmd "pg_isready -U dw" --health-interval 5s --health-retries 10
  env: {DBT_USER: dw, DBT_PASSWORD: dw, DBT_SCHEMA: ci, DBT_TARGET: dev}
  defaults: {run: {working-directory: dbt}}
  steps:
    - uses: actions/checkout@v4      # same majors as the repo ci.yml
    - uses: actions/setup-python@v5
      with: {python-version: "3.12"}
    - run: pip install "dbt-core~=1.11.0" "dbt-postgres~=1.11.0"
    - run: dbt deps && dbt parse
    # needs raw.* tables: create them from fixtures/ingestion first, or stop at parse
    - run: dbt build --empty --exclude-resource-type unit_test && dbt build
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `require-dbt-version` | none | `[">=1.11.0", "<1.12.0"]` matches the pins |
| `package-lock.yml` | created by `dbt deps` | Commit it: reproducible package versions |
| `DBT_TARGET` | `dev` | Read by `profiles.yml` `target:`; `prod` in Airflow |
| `--threads` | profile `threads` | Parallel nodes |
| `--fail-fast` / `-x` | off | Stop at first failure (CI) |
| `DBT_ENGINE_*` env vars | - | 1.11 prefix, e.g. `DBT_ENGINE_STATE`, `DBT_ENGINE_PROFILES_DIR` |
| `DBT_SEND_ANONYMOUS_USAGE_STATS` | `true` | Set `false` in containers/CI |

## Example Usage

```bash
# slim CI / fast dev loop: compare with prod artifacts (copy, never point at target/)
mkdir -p state && cp path/to/prod/target/manifest.json state/
dbt ls -s "state:modified" --state state                    # what changed (verified offline)
dbt build -s "state:modified+" --defer --state state        # unchanged parents read from prod
dbt retry                                                   # re-run only failed nodes of last run
dbt build -s "result:error+" --state target_prev/           # explicit alternative
dbt run -s fct_vendas --empty                               # schema-only build (0 rows)
dbt clean && dbt deps                                       # reset packages / artifacts
```

Airflow runs the same commands from its dbt venv (`--target prod`), see the docker
KB's Airflow pattern; the standalone container is `docker compose run --rm dbt build`.
Verified in scratch: `dbt deps` (dbt_utils 1.4.1), `dbt parse`, `dbt build` (46 nodes),
`state:modified` selection; the CI YAML itself was not executed.

## See Also

- [project-structure](../concepts/project-structure.md)
- [profiles-targets](../concepts/profiles-targets.md)
- [dbt-runner-container (docker KB)](../../docker/patterns/dbt-runner-container.md)
- [airflow-local-compose (docker KB)](../../docker/patterns/airflow-local-compose.md)
- [project-setup-uv (python KB)](../../python/patterns/project-setup-uv.md)
