# Images, Layers and Build Cache

> **Purpose**: Understand how images are built from cached layers so rebuilds stay fast and images stay small
> **Confidence**: 0.95
> **MCP Validated**: 2026-10-09

## Overview

An image is an immutable, ordered stack of read-only layers; each filesystem-changing
Dockerfile instruction (`RUN`, `COPY`, `ADD`) adds one layer. BuildKit reuses a cached
layer when the instruction and its inputs are unchanged; once one layer is invalidated,
**every layer after it is rebuilt**. So order instructions from least to most frequently
changing: base image, system packages, dependency manifests + install, then source code.

## The Pattern

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim                     # 1. base: changes rarely (pin the tag)

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*           # 2. OS deps: same layer as update + cleanup

WORKDIR /app
COPY pyproject.toml uv.lock ./            # 3. manifests only -> dependency layer is
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,from=ghcr.io/astral-sh/uv:0.13.0,source=/uv,target=/bin/uv \
    uv sync --locked --no-install-project # reused until the lockfile changes

COPY src/ ./src/                          # 4. source: changes on every commit,
                                          #    invalidates only this layer onward
```

```bash
docker image history dw-ingest:dev        # list layers and their sizes
docker build --progress=plain -t dw-ingest:dev .   # shows CACHED vs executed steps
docker builder prune                      # drop build cache when disk is tight
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `FROM python:3.12-slim` | Base layers pulled once | `slim` = Debian minus extras; avoid `alpine` for wheels (musl) |
| `COPY . .` before `RUN install` | Deps reinstall on any file edit | Copy manifests first |
| `RUN --mount=type=cache,target=...` | Persistent package cache across builds | Not stored in the image |
| `RUN --mount=type=bind,source=f,target=f` | File visible only during that `RUN` | No layer for the file |
| `docker build --no-cache` | Rebuild every layer | Use to pick up new upstream packages |
| `image:tag` | Mutable pointer | `image@sha256:...` is immutable |

## Common Mistakes

### Wrong

```dockerfile
COPY . /app                               # any edit busts the cache below
RUN pip install -r /app/requirements.txt  # full reinstall on every build
RUN apt-get update                        # cached alone -> stale index later
RUN apt-get install -y libpq5
```

### Correct

```dockerfile
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*
```

## Related

- [dockerfile-best-practices](../concepts/dockerfile-best-practices.md)
- [python-uv-dockerfile](../patterns/python-uv-dockerfile.md)
