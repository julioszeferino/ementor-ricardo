# Dockerfile Best Practices

> **Purpose**: Write small, reproducible, non-root images: multi-stage, pinned bases, `.dockerignore`, exec-form commands
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

A good Dockerfile builds in one stage (compilers, package managers, caches) and ships
only the runtime artifacts in a slim final stage. Pin base images to a specific tag
(or digest), exclude junk from the build context with `.dockerignore`, run as a
non-root user with an explicit UID, and use the JSON exec form for `ENTRYPOINT`/`CMD`
so the process is PID 1 and receives `SIGTERM` on `docker compose stop`.

## The Pattern

```dockerfile
# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS builder      # stage 1: build tools live here
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:${PYTHON_VERSION}-slim AS runtime      # stage 2: same base => same python path
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app src/ /app/src/
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
USER app                                           # explicit non-root UID 10001
ENTRYPOINT ["python", "-m", "dw"]                  # exec form: PID 1 gets signals
CMD ["--help"]                                     # default args, overridable
```

```gitignore
# .dockerignore (next to the Dockerfile / build context root)
.git
.venv
__pycache__/
*.pyc
.env
.env.*
data/
logs/
target/          # dbt build artifacts
dbt_packages/
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `FROM ... AS builder` + `COPY --from=builder` | Final image without build deps | Smaller attack surface |
| `docker build --target builder .` | Stop at a named stage | Debug intermediate stages |
| `FROM python:3.12-slim` vs `python:latest` | Reproducible vs drifting base | Pin digest for full immutability |
| `USER 10001` | Non-root process | Fixed UID simplifies volume permissions |
| `CMD ["a","b"]` vs `CMD a b` | Exec form vs `/bin/sh -c` wrapper | Shell form swallows signals |
| `COPY` vs `ADD` | Plain copy vs remote/tar extraction | Prefer `COPY` |
| `WORKDIR /app` | Absolute working dir | Never `RUN cd ...` |
| `.env` in `.dockerignore` | Secrets kept out of image layers | Layers are readable by anyone with the image |

## Common Mistakes

### Wrong

```dockerfile
FROM python:latest
COPY . .                      # copies .git, .venv, .env into the image
RUN pip install -r requirements.txt
ENV DB_PASSWORD=secret        # baked into image metadata forever
CMD python -m dw              # shell form, runs as root
```

### Correct

```dockerfile
FROM python:3.12-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
USER 10001
CMD ["python", "-m", "dw"]    # password injected at runtime via env/secret
```

## Related

- [images-layers-cache](../concepts/images-layers-cache.md)
- [env-vars-secrets](../concepts/env-vars-secrets.md)
- [python-uv-dockerfile](../patterns/python-uv-dockerfile.md)
