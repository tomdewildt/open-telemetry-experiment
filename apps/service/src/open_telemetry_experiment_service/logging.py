from __future__ import annotations

import logging
import sys

import loguru
from asgi_correlation_id.context import correlation_id

from open_telemetry_experiment_service.config import Environment, LogLevel


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Map the standard logging level name to a loguru level
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Patch caller info from the log record to avoid misresolved frames
        patched = loguru.logger.patch(
            lambda r: r.update(
                name=record.name,
                function=record.funcName,
                line=record.lineno,
            ),
        )
        patched.opt(exception=record.exc_info).log(level, record.getMessage())


def _correlation_id_patcher(record: loguru.Record) -> None:
    record["extra"]["correlation_id"] = correlation_id.get() or ""


def _log_format(record: loguru.Record) -> str:
    base = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"  # noqa: E501
    if record["extra"].get("correlation_id"):
        base += " | <blue>[{extra[correlation_id]}]</blue>"
    return base + " - <level>{message}</level>\n{exception}"


def init_logging(env: Environment, level: LogLevel) -> None:
    logging.root.handlers = [_InterceptHandler()]
    logging.root.setLevel(logging.DEBUG)  # Ensure standard logging does not filter anything out

    # Strip handlers of standard loggers and propagate them to the intercept handler
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Disable uvicorn access log (handled by middleware)
    logging.getLogger("uvicorn.access").disabled = True

    should_serialize = env == Environment.PROD
    loguru.logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "level": level.upper(),
                "format": "{message}" if should_serialize else _log_format,
                "serialize": should_serialize,
            },
        ],
        patcher=_correlation_id_patcher,
    )
