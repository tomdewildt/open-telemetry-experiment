import json
import random

import httpx
from asgi_correlation_id.context import correlation_id as correlation_id_ctx
from fastapi import HTTPException
from loguru import logger
from saq import Queue

from open_telemetry_experiment_worker.config import config
from open_telemetry_experiment_worker.repositories import CallbackRepository, ExternalApiRepository, ServiceRepository


class EnqueueService:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue

    async def enqueue(self, request_id: str, text: str, callback_url: str) -> str:
        logger.info("Enqueueing job (request_id={request_id})", request_id=request_id)

        if _should_fail(config.API_FAILURE_RATE):
            logger.error("Injected failure while enqueueing (request_id={request_id})", request_id=request_id)
            raise HTTPException(status_code=500, detail="injected failure")

        job = await self._queue.enqueue(
            "process_task",
            request_id=request_id,
            text=text,
            callback_url=callback_url,
            correlation_id=correlation_id_ctx.get(),
        )
        return job.key if job else ""


class TaskService:
    def __init__(
        self,
        external: ExternalApiRepository,
        service: ServiceRepository,
        callback: CallbackRepository,
    ) -> None:
        self._external = external
        self._service = service
        self._callback = callback

    async def process(self, request_id: str, text: str, callback_url: str) -> str:
        logger.info("Processing job (request_id={request_id})", request_id=request_id)
        try:
            if _should_fail(config.WORKER_FAILURE_RATE):
                raise RuntimeError("injected failure")
            fact = await self._external.get_fact()
            processed = await self._service.process(text)
            result = json.dumps({**processed, "fact": fact})
        except (httpx.HTTPError, RuntimeError) as error:
            logger.error("Job failed (request_id={request_id}, error={error})", request_id=request_id, error=error)
            await self._callback.send(callback_url, {"request_id": request_id, "status": "failed", "error": str(error)})
            raise

        logger.info("Job done (request_id={request_id})", request_id=request_id)
        await self._callback.send(callback_url, {"request_id": request_id, "status": "done", "result": result})
        return result


def _should_fail(rate: float) -> bool:
    return random.random() < rate
