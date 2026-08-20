import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from loguru import logger
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    OsResourceDetector,
    ProcessResourceDetector,
    Resource,
    ServiceInstanceIdResourceDetector,
    _HostResourceDetector,
    get_aggregated_resources,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from open_telemetry_experiment_service.config import config


def _flatten(key: str, value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        flattened: dict[str, Any] = {}
        for sub_key, sub_value in value.items():
            flattened.update(_flatten(f"{key}.{sub_key}", sub_value))
        return flattened
    return {key: value}


class _FlatteningLoggingHandler(LoggingHandler):
    # Otel attributes cannot hold objects, so we flatten the extra dict to a single level with dot notation for nested
    # keys.
    @staticmethod
    def _get_attributes(record: logging.LogRecord) -> dict[str, Any]:
        attributes = dict(LoggingHandler._get_attributes(record))
        extra = attributes.pop("extra", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                attributes.update(_flatten(key, value))
        return attributes


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


def init_telemetry(app: FastAPI) -> None:
    if not config.OTEL_ENABLED:
        return

    resource = get_aggregated_resources(
        [
            _HostResourceDetector(),
            OsResourceDetector(),
            ProcessResourceDetector(),
            ServiceInstanceIdResourceDetector(),
        ],
    ).merge(
        Resource.create(
            {
                "service.name": f"@{config.OTEL_SERVICE_NAMESPACE}/{config.OTEL_SERVICE_NAME}",
                "service.version": config.VERSION,
                "deployment.environment": config.ENV.value,
            },
        ),
    )

    # Traces
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(TraceIdRatioBased(config.OTEL_SAMPLE_RATIO)),
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{config.OTEL_ENDPOINT}/v1/traces"))
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{config.OTEL_ENDPOINT}/v1/metrics")),
        ],
    )
    metrics.set_meter_provider(meter_provider)

    FastAPIInstrumentor.instrument_app(app, exclude_spans=["send", "receive"])

    # Logs
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{config.OTEL_ENDPOINT}/v1/logs"))
    )
    set_logger_provider(logger_provider)
    logger.add(
        _FlatteningLoggingHandler(level=logging.NOTSET, logger_provider=logger_provider),
        level=config.LOG_LEVEL.upper(),
        format="{message}",
    )
