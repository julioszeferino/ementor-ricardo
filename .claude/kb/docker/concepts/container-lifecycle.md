# Container Lifecycle

> **Purpose**: Know the states a container moves through and which command (and restart policy) drives each transition
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A container is a running (or stopped) instance of an image plus a thin writable layer.
States: `created` -> `running` -> (`paused`) -> `exited` -> removed. Anything written to
the writable layer disappears on removal, so persistent data must live in a volume. On
`stop`, Docker sends `SIGTERM` to PID 1, waits a grace period (10 s by default), then
`SIGKILL`s; long-running services should handle `SIGTERM` and run as PID 1 (exec form)
or behind an init (`init: true`).

## The Pattern

```yaml
# compose.yaml -- lifecycle-related service keys
services:
  postgres:
    image: postgres:18
    restart: unless-stopped        # survives daemon restarts; not after `stop`
    stop_grace_period: 30s         # time between SIGTERM and SIGKILL
  ingest:
    build: ./ingest
    restart: "no"                  # batch job: run once, exit code is the result
    init: true                     # tiny init as PID 1: forwards signals, reaps zombies
```

```bash
docker compose up -d               # create + start (recreates if config/image changed)
docker compose ps -a               # include exited containers and their exit codes
docker compose stop postgres       # SIGTERM -> grace -> SIGKILL; container kept
docker compose start postgres      # restart same container (writable layer intact)
docker compose restart postgres    # stop + start, does NOT apply compose.yaml edits
docker compose run --rm ingest     # one-off container, removed on exit
docker compose down                # stop + remove containers and networks (volumes kept)
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `restart: "no"` | Never restarted | Default; use for batch/one-off jobs |
| `restart: on-failure:3` | Restart on non-zero exit, max 3 | Flaky jobs |
| `restart: unless-stopped` | Restart unless manually stopped | Long-running local services |
| `restart: always` | Restart until removed | Official Airflow compose uses it |
| Exit code `0` / `1` / `137` / `143` | OK / app error / SIGKILL (OOM?) / SIGTERM | Check `docker compose ps -a` |
| `docker compose restart svc` | Same config | Edits need `up -d` to recreate |
| `docker compose up -d --force-recreate svc` | New container | Writable layer discarded |

## Common Mistakes

### Wrong

```bash
docker compose exec postgres bash -c "echo 'tuning' >> /etc/some.conf"  # lost on recreate
docker compose restart ingest       # expecting new env vars from compose.yaml to apply
```

### Correct

```bash
# put config in compose.yaml / a bind-mounted file, then recreate
docker compose up -d ingest         # detects config change and recreates the container
```

## Related

- [volumes-bind-mounts](../concepts/volumes-bind-mounts.md)
- [compose-services-healthchecks](../concepts/compose-services-healthchecks.md)
- [compose-dev-workflow](../patterns/compose-dev-workflow.md)
