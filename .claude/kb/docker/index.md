# Docker Knowledge Base

> **Purpose**: Docker + Docker Compose (Compose Specification, `docker compose` v2 CLI) for the local data stack -- Python ingestion, Postgres warehouse, dbt and Airflow
> **MCP Validated**: 2026-10-09

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/images-layers-cache.md](concepts/images-layers-cache.md) | Layers, cache invalidation order, BuildKit cache/bind mounts |
| [concepts/dockerfile-best-practices.md](concepts/dockerfile-best-practices.md) | Multi-stage, pinned bases, non-root `USER`, `.dockerignore`, exec form |
| [concepts/container-lifecycle.md](concepts/container-lifecycle.md) | States, stop/SIGTERM, restart policies, `restart` vs `up -d` |
| [concepts/volumes-bind-mounts.md](concepts/volumes-bind-mounts.md) | Named volumes for data, bind mounts for code; Postgres 18 path change |
| [concepts/networking.md](concepts/networking.md) | `<project>_default` network, service DNS, container vs host ports |
| [concepts/compose-services-healthchecks.md](concepts/compose-services-healthchecks.md) | `depends_on` conditions, healthchecks, profiles, `--wait` |
| [concepts/env-vars-secrets.md](concepts/env-vars-secrets.md) | `.env` interpolation vs `environment`/`env_file`, precedence, secrets |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/python-uv-dockerfile.md](patterns/python-uv-dockerfile.md) | Multi-stage uv image for the ingestion package, non-root, cached deps |
| [patterns/postgres-service.md](patterns/postgres-service.md) | Warehouse Postgres: named volume, healthcheck, secret, init scripts |
| [patterns/airflow-local-compose.md](patterns/airflow-local-compose.md) | Airflow 3.3 LocalExecutor stack derived from the official compose file |
| [patterns/dbt-runner-container.md](patterns/dbt-runner-container.md) | Pinned dbt-postgres image + env-driven `profiles.yml` |
| [patterns/compose-dev-workflow.md](patterns/compose-dev-workflow.md) | Makefile wrappers, debugging commands, troubleshooting table |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/compose-stack.yaml](specs/compose-stack.yaml) | Required `compose.yaml` keys for this stack and their validation rules |

### Examples

| File | Purpose |
|------|---------|
| [examples/tests/docker-kb-checks.json](examples/tests/docker-kb-checks.json) | `docker compose config` behaviors and version pins backing KB claims |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Images are cached layers** | Order Dockerfile steps from stable to volatile; deps before source |
| **Containers are disposable** | Anything not in a volume is lost on recreate; config lives in `compose.yaml` |
| **Readiness, not start** | `depends_on` + `condition: service_healthy` + a real healthcheck |
| **Service names are hostnames** | Containers talk to `postgres:5432`; `ports:` is only for the host |
| **Config at runtime** | `.env` interpolation and secrets, never credentials baked into images |
| **Pin everything** | Base images, uv, Airflow, dbt and Postgres majors |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/container-lifecycle.md, concepts/images-layers-cache.md, concepts/volumes-bind-mounts.md, concepts/networking.md |
| **Intermediate** | concepts/dockerfile-best-practices.md, concepts/compose-services-healthchecks.md, concepts/env-vars-secrets.md, patterns/postgres-service.md, patterns/compose-dev-workflow.md |
| **Advanced** | patterns/python-uv-dockerfile.md, patterns/dbt-runner-container.md, patterns/airflow-local-compose.md, specs/compose-stack.yaml |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| kb-architect | index.md, specs/compose-stack.yaml | Audit/extend this domain |
| Any coding agent | patterns/*.md, quick-reference.md | Write Dockerfiles and `compose.yaml` for the stack |
| Python work | ../python/patterns/project-setup-uv.md + patterns/python-uv-dockerfile.md | Containerize the uv project |

Out of scope: Swarm, Kubernetes, registries/CI publishing.
