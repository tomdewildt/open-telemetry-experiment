from typing import Any

import httpx

from open_telemetry_experiment_worker.config import config
from open_telemetry_experiment_worker.instrumentation import SaqQueueMetrics, instrument_saq_job
from open_telemetry_experiment_worker.logging import init_logging
from open_telemetry_experiment_worker.queue import queue
from open_telemetry_experiment_worker.repositories import (
    HttpxCallbackRepository,
    HttpxExternalApiRepository,
    HttpxServiceRepository,
)
from open_telemetry_experiment_worker.services import TaskService
from open_telemetry_experiment_worker.telemetry import init_worker_telemetry


async def startup(ctx: dict[str, Any]) -> None:
    init_logging(config.ENV, config.LOG_LEVEL)
    init_worker_telemetry()
    if config.OTEL_ENABLED:
        ctx["queue_metrics"] = SaqQueueMetrics(queue)
        ctx["queue_metrics"].start()
    http_client = httpx.AsyncClient(timeout=15.0)
    ctx["http_client"] = http_client
    ctx["task_service"] = TaskService(
        HttpxExternalApiRepository(http_client, config.EXTERNAL_API_BASE_URL),
        HttpxServiceRepository(http_client, config.SERVICE_BASE_URL),
        HttpxCallbackRepository(http_client),
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    metrics = ctx.get("queue_metrics")
    if metrics:
        metrics.stop()
    await ctx["http_client"].aclose()


async def process_task(
    ctx: dict[str, Any],
    *,
    request_id: str,
    text: str,
    callback_url: str,
    otel_context: dict[str, str] | None = None,
) -> str:
    task_service: TaskService = ctx["task_service"]
    async with instrument_saq_job(ctx["job"], otel_context):
        return await task_service.process(request_id, text, callback_url)


settings = {
    "queue": queue,
    "functions": [process_task],
    "concurrency": 5,
    "startup": startup,
    "shutdown": shutdown,
}
