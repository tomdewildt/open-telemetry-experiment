import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from loguru import logger
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from open_telemetry_experiment_service.config import config


def init_telemetry(app: FastAPI) -> None:
    if not config.OTEL_ENABLED:
        return

    resource = Resource.create(
        {
            "service.name": f"@{config.OTEL_SERVICE_NAMESPACE}/{config.OTEL_SERVICE_NAME}",
            "service.version": config.VERSION,
            "deployment.environment": config.ENV.value,
        },
    )

    # Traces
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{config.OTEL_ENDPOINT}/v1/traces"))
    )
    trace.set_tracer_provider(tracer_provider)
    FastAPIInstrumentor.instrument_app(app, exclude_spans=["send", "receive"])

    # Logs
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{config.OTEL_ENDPOINT}/v1/logs"))
    )
    set_logger_provider(logger_provider)
    logger.add(
        LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider),
        level=config.LOG_LEVEL.upper(),
        format="{message}",
    )


def traced(name: str | Callable[..., Any] | None = None) -> Any:
    def wrap(func: Callable[..., Any], span_name: str) -> Callable[..., Any]:
        tracer = trace.get_tracer(__name__)

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name):
                return func(*args, **kwargs)

        return sync_wrapper

    if callable(name):
        return wrap(name, name.__qualname__)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return wrap(func, name or func.__qualname__)

    return decorator
