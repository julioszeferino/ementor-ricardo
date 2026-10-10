# Application Logging Setup

> **Purpose**: Configure logging once at the entry point, with env-driven level and optional JSON output for log aggregators
> **MCP Validated**: 2026-10-09

## When to Use

- Any CLI, scheduled job or container entry point of the pipeline
- Logs are shipped to CloudWatch/Datadog/Loki and must be machine-parsable
- Different verbosity is needed per environment without code changes

## Implementation

```python
"""dw/logging_config.py -- call configure_logging() once, from main()."""
import json
import logging
import logging.config
import os
from datetime import UTC, datetime
from typing import Any, override

_RESERVED = set(vars(logging.makeLogRecord({})))


class JsonFormatter(logging.Formatter):
    """One JSON object per line; includes `extra={...}` fields."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload |= {k: v for k, v in vars(record).items()
                    if k not in _RESERVED and not k.startswith("_")}
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str | None = None, *, json_output: bool | None = None) -> None:
    root_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    if json_output is None:
        json_output = os.getenv("LOG_FORMAT", "text") == "json"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,          # default True would mute library loggers
        "formatters": {
            "text": {"format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s"},
            "json": {"()": JsonFormatter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "json" if json_output else "text",
            },
        },
        "loggers": {
            "urllib3": {"level": "WARNING"},        # quiet noisy dependencies
            "botocore": {"level": "WARNING"},
        },
        "root": {"level": root_level, "handlers": ["console"]},
    })
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Root level: DEBUG, INFO, WARNING, ERROR |
| `LOG_FORMAT` | `text` | `json` switches to one-JSON-object-per-line |
| `disable_existing_loggers` | `False` (set explicitly) | stdlib default is `True` |
| `loggers.<name>.level` | inherited | Per-dependency verbosity overrides |

## Example Usage

```python
# dw/__main__.py
import logging
from dw.logging_config import configure_logging

logger = logging.getLogger(__name__)

def main() -> None:
    configure_logging()
    logger.info("load finished", extra={"table": "sales", "rows": 1200})
    # LOG_FORMAT=json -> {"ts": "...", "level": "INFO", "logger": "__main__",
    #                     "msg": "load finished", "table": "sales", "rows": 1200}

if __name__ == "__main__":
    main()
```

## See Also

- [error-handling-retry](../patterns/error-handling-retry.md)
- [logging](../concepts/logging.md)
