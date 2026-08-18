from typing import Any

import httpx
from asgi_correlation_id.context import correlation_id as correlation_id_ctx

from open_telemetry_experiment_worker.config import config
from open_telemetry_experiment_worker.logging import init_logging
from open_telemetry_experiment_worker.queue import queue
from open_telemetry_experiment_worker.repositories import (
    HttpxCallbackRepository,
    HttpxExternalApiRepository,
    HttpxServiceRepository,
)
from open_telemetry_experiment_worker.services import TaskService


async def _forward_correlation_id(request: httpx.Request) -> None:
    cid = correlation_id_ctx.get()
    if cid:
        request.headers["X-Request-ID"] = cid


async def startup(ctx: dict[str, Any]) -> None:
    init_logging(config.ENV, config.LOG_LEVEL)
    http_client = httpx.AsyncClient(timeout=15.0, event_hooks={"request": [_forward_correlation_id]})
    ctx["http_client"] = http_client
    ctx["task_service"] = TaskService(
        HttpxExternalApiRepository(http_client, config.EXTERNAL_API_BASE_URL),
        HttpxServiceRepository(http_client, config.SERVICE_BASE_URL),
        HttpxCallbackRepository(http_client),
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["http_client"].aclose()


async def process_task(
    ctx: dict[str, Any], *, request_id: str, text: str, callback_url: str, correlation_id: str | None = None
) -> str:
    if correlation_id:
        correlation_id_ctx.set(correlation_id)
    task_service: TaskService = ctx["task_service"]
    return await task_service.process(request_id, text, callback_url)


settings = {
    "queue": queue,
    "functions": [process_task],
    "concurrency": 5,
    "startup": startup,
    "shutdown": shutdown,
}
