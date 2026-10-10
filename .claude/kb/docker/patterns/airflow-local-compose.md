# Airflow 3 on Compose (LocalExecutor)

> **Purpose**: Run Airflow locally with a lean, production-shaped stack: LocalExecutor + dedicated metadata Postgres, derived from the official compose file
> **MCP Validated**: 2026-10-09

## When to Use

- Orchestrating the ingestion and dbt runs of the local warehouse on a laptop
- You need the Airflow 3 components (api-server, scheduler, dag-processor) without Celery/Redis
- Starting point; the official file (`curl -LfO https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml`) uses CeleryExecutor and is explicitly **not** production-secure

## Implementation

```yaml
# compose.yaml (excerpt) -- add next to the `postgres` warehouse service
x-airflow-common: &airflow-common
  build: ./airflow                          # Dockerfile below (adds dbt)
  image: dw-airflow:3.3.2
  environment: &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor  # tasks run as subprocesses of the scheduler
    AIRFLOW__CORE__AUTH_MANAGER: airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@airflow-db/airflow
    AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY:-}
    AIRFLOW__CORE__LOAD_EXAMPLES: "false"
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "true"
    AIRFLOW__CORE__EXECUTION_API_SERVER_URL: http://airflow-apiserver:8080/execution/
    AIRFLOW__API_AUTH__JWT_SECRET: ${AIRFLOW_JWT_SECRET:-change-me-local-only}
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: "true"
    AIRFLOW_CONN_DW_POSTGRES: postgres://${POSTGRES_USER:-dw}:${DW_PASSWORD:?set DW_PASSWORD}@postgres:5432/${POSTGRES_DB:-warehouse}
    DBT_PROFILES_DIR: /opt/dbt              # profiles.yml from dbt-runner-container
    DBT_USER: ${POSTGRES_USER:-dw}
    DBT_PASSWORD: ${DW_PASSWORD:?set DW_PASSWORD}
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - ./dbt:/opt/dbt                        # dbt writes target/ and logs/ here
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on: &airflow-common-depends-on
    airflow-db:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  airflow-db:                               # metadata DB, isolated from warehouse data
    image: postgres:16                      # same major as the official compose file
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - airflow-db:/var/lib/postgresql/data # <= 17 path
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: unless-stopped

  airflow-init:                             # one-shot: migrate DB, create admin user
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /opt/airflow/{logs,dags,plugins}
        chown -R "${AIRFLOW_UID:-50000}:0" /opt/airflow/{logs,dags,plugins}
        exec /entrypoint airflow version
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_MIGRATE: "true"
      _AIRFLOW_WWW_USER_CREATE: "true"
      _AIRFLOW_WWW_USER_USERNAME: ${AIRFLOW_ADMIN_USER:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${AIRFLOW_ADMIN_PASSWORD:-airflow}
    user: "0:0"

  airflow-apiserver:                        # UI + REST API + task execution API
    <<: *airflow-common
    command: api-server
    ports: ["8080:8080"]
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/api/v2/monitor/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type SchedulerJob --hostname "$${HOSTNAME}"']
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-dag-processor:                    # parses DAG files (separate process in Airflow 3)
    <<: *airflow-common
    command: dag-processor
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type DagProcessorJob --hostname "$${HOSTNAME}"']
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

volumes:
  airflow-db: {}
```

```dockerfile
# airflow/Dockerfile -- extend the official image; dbt in its own venv (no dep clashes)
FROM apache/airflow:3.3.2
USER root
RUN python -m venv /opt/dbt-venv \
 && /opt/dbt-venv/bin/pip install --no-cache-dir "dbt-core~=1.11.0" "dbt-postgres~=1.11.0"
USER airflow
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `AIRFLOW_UID` (`.env`) | `50000` | Set to `$(id -u)` on Linux so logs/dags are owned by you |
| `AIRFLOW__CORE__EXECUTOR` | official: `CeleryExecutor` | `LocalExecutor` drops redis + worker containers |
| `AIRFLOW__CORE__EXECUTION_API_SERVER_URL` | - | Airflow 3 tasks report via the api-server; use its service name |
| `AIRFLOW__API_AUTH__JWT_SECRET` | - | Set it explicitly; must be identical across all components |
| `AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK` | `false` | Health server on `:8974/health` (kept from official file) |
| `DW_PASSWORD` (`.env`) | required | Warehouse password for the Airflow connection and dbt; same value as `secrets/pg_password.txt` |
| `AIRFLOW_CONN_<ID>` | - | Connection as URI env var -> `conn_id="dw_postgres"` |
| `_AIRFLOW_DB_MIGRATE` / `_AIRFLOW_WWW_USER_CREATE` | unset | Image entrypoint hooks used only by `airflow-init` |
| triggerer | omitted | Add a `command: triggerer` service if you use deferrable operators |

## Example Usage

```bash
mkdir -p dags logs plugins dbt && echo "AIRFLOW_UID=$(id -u)" >> .env
docker compose up -d --build           # UI: http://localhost:8080 (airflow / airflow)
docker compose ps                      # airflow-init: Exited (0); others: (healthy)
docker compose exec airflow-scheduler airflow dags list      # CLI in running container
```

```python
# dags/dw_daily.py -- Airflow 3 imports
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

with DAG(dag_id="dw_daily", schedule="@daily", catchup=False):
    BashOperator(task_id="dbt_build",
                 bash_command="cd /opt/dbt && /opt/dbt-venv/bin/dbt build --target docker")
```

## See Also

- [dbt-runner-container](../patterns/dbt-runner-container.md)
- [postgres-service](../patterns/postgres-service.md)
- [compose-services-healthchecks](../concepts/compose-services-healthchecks.md)
- [compose-dev-workflow](../patterns/compose-dev-workflow.md)
