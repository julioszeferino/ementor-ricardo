# Networking and Service DNS

> **Purpose**: Connect services by name on Compose networks and expose only what the host needs
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

`docker compose up` creates a user-defined bridge network `<project>_default` and
attaches every service. Each service name is registered in Docker's embedded DNS, so
containers reach each other as `postgres:5432` -- always the **container** port.
`ports:` only publishes a port to the host (your laptop, DBeaver, the browser); it is
not needed for container-to-container traffic. From the host, use `localhost:<HOST_PORT>`.

## The Pattern

```yaml
services:
  postgres:
    image: postgres:18
    ports:
      - "127.0.0.1:5433:5432"   # host:5433 -> container:5432, loopback only
    networks: [backend]
  ingest:
    build: ./ingest
    environment:
      DB_HOST: postgres          # service name, resolved by Docker DNS
      DB_PORT: "5432"            # CONTAINER port, not 5433
    networks: [backend]
  airflow-apiserver:
    image: apache/airflow:3.3.2
    ports:
      - "8080:8080"              # UI at http://localhost:8080
    networks: [backend, frontend]

networks:
  backend: {}                    # services only talk if they share a network
  frontend: {}
```

```bash
docker compose exec ingest getent hosts postgres     # check DNS resolution
docker network ls                                    # <project>_backend, ...
psql "postgresql://dw:dw@localhost:5433/warehouse"   # from the host
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| No `networks:` key | All services on `<project>_default` | Enough for a local stack |
| `ports: ["5433:5432"]` | Host 5433 -> container 5432 | Binds all host interfaces |
| `ports: ["127.0.0.1:5433:5432"]` | Host loopback only | Safer on shared Wi-Fi |
| `expose: ["6379"]` | Documentation only | Not published to host |
| Container -> `localhost` | The container itself | Not the host, not other services |
| Container -> host service | `host.docker.internal` | Built into Docker Desktop; elsewhere add `extra_hosts: ["host.docker.internal:host-gateway"]` |
| `links:` | Legacy | Not needed for service discovery |

## Common Mistakes

### Wrong

```yaml
services:
  ingest:
    environment:
      DB_HOST: localhost      # resolves to the ingest container itself
      DB_PORT: "5433"         # host-published port, unreachable from containers
```

### Correct

```yaml
services:
  ingest:
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
```

## Related

- [compose-services-healthchecks](../concepts/compose-services-healthchecks.md)
- [compose-dev-workflow](../patterns/compose-dev-workflow.md)
