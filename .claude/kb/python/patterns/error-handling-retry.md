# Error Handling with Retry and Backoff

> **Purpose**: Retry transient failures (network, throttling) with exponential backoff while failing fast on permanent errors
> **MCP Validated**: 2026-10-09

## When to Use

- Calling APIs, object storage or databases that occasionally time out or throttle
- Pipeline steps that are idempotent and therefore safe to re-run
- You need retries without adding a dependency (otherwise consider `tenacity`)

## Implementation

```python
"""dw/retry.py -- stdlib-only retry decorator with exponential backoff + jitter."""
import functools
import logging
import random
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base for all project errors."""


class TransientError(PipelineError):
    """Temporary failure; safe to retry."""


class PermanentError(PipelineError):
    """Bad input/config; retrying will not help."""


def retry[**P, R](
    *,
    attempts: int = 4,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (TransientError, TimeoutError, ConnectionError),
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as err:
                    if attempt == attempts:
                        err.add_note(f"gave up after {attempts} attempts")
                        raise
                    delay = min(max_delay, base_delay * 2 ** (attempt - 1))
                    delay *= random.uniform(0.5, 1.0)          # jitter avoids thundering herd
                    logger.warning("retrying func=%s attempt=%d/%d delay=%.2fs error=%r",
                                   func.__qualname__, attempt, attempts, delay, err)
                    sleep(delay)
            raise AssertionError("unreachable")
        return wrapper
    return decorator
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `attempts` | `4` | Total calls including the first one |
| `base_delay` | `0.5` | Seconds before the 1st retry; doubles each attempt |
| `max_delay` | `30.0` | Upper bound for a single wait |
| `retry_on` | `(TransientError, TimeoutError, ConnectionError)` | Only these are retried; all else propagates immediately |
| `sleep` | `time.sleep` | Injectable so tests run instantly |

## Example Usage

```python
import urllib.error
import urllib.request

from dw.retry import PermanentError, TransientError, retry

@retry(attempts=5, base_delay=1.0)
def fetch(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read()
    except urllib.error.HTTPError as err:
        if err.code in {429, 500, 502, 503, 504}:
            raise TransientError(f"HTTP {err.code} for {url}") from err
        raise PermanentError(f"HTTP {err.code} for {url}") from err

# Test without real waiting:
calls: list[float] = []

@retry(attempts=3, sleep=calls.append)
def flaky() -> str:
    if len(calls) < 2:
        raise TransientError("boom")
    return "ok"

assert flaky() == "ok" and len(calls) == 2
```

## See Also

- [logging-setup](../patterns/logging-setup.md)
- [exceptions](../concepts/exceptions.md)
