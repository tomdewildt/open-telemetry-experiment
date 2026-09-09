import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import get_args

from loguru import logger
from opentelemetry import metrics, trace
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.propagate import extract, inject
from saq import Job, Queue
from saq.types import CountKind

# Metric instruments are long-lived handles keyed by name: created once at import and shared by every job, rather than
# re-registered on each call.
_meter = metrics.get_meter("saq")
_jobs = _meter.create_counter("saq.jobs", description="Number of processed jobs")
_job_duration = _meter.create_histogram("saq.job.duration", unit="s", description="Job processing duration")
_job_wait = _meter.create_histogram("saq.job.wait", unit="s", description="Time a job waited before processing")
_job_attempts = _meter.create_counter("saq.job.attempts", description="Number of job execution attempts")


def otel_context() -> dict[str, str]:
    carrier: dict[str, str] = {}
    inject(carrier)
    return carrier


@asynccontextmanager
async def instrument_saq_job(job: Job, carrier: dict[str, str] | None = None) -> AsyncGenerator[None]:
    tracer = trace.get_tracer(__name__)
    start = time.perf_counter()
    status = "done"

    # Continue the trace started on the enqueue side
    with tracer.start_as_current_span(job.function, context=extract(carrier or {})):
        try:
            yield
        except Exception:
            status = "failed"
            raise
        finally:
            attributes = {"job": job.function, "status": status}
            _jobs.add(1, attributes)

            # SAQ sets the completion timestamp only after this block returns, so we time the work
            # ourselves instead of reading job.duration("process")
            _job_duration.record(time.perf_counter() - start, attributes)
            _job_attempts.add(1, {**attributes, "retry": job.attempts > 1})

            # Wait time comes straight from SAQ's timestamps (started - queued, in milliseconds).
            wait = job.duration("start")
            if wait is not None:
                _job_wait.record(wait / 1000, attributes)


class SaqQueueMetrics:
    # Observable gauges are read synchronously by the SDK, so a background task polls SAQ and caches
    # the latest snapshot for the gauge callbacks to return.
    _STATES: tuple[CountKind, ...] = get_args(CountKind)

    def __init__(self, queue: Queue, poll_interval: float = 5.0) -> None:
        self._queue = queue
        self._poll_interval = poll_interval
        self._depth_by_state: dict[CountKind, int] = {}
        self._worker_count = 0
        self._poll_task: asyncio.Task[None] | None = None

        _meter.create_observable_gauge(
            "saq.queue.depth",
            callbacks=[self._observe_depth],
            description="Jobs by state",
        )
        _meter.create_observable_gauge(
            "saq.queue.workers",
            callbacks=[self._observe_worker_count],
            description="Live workers",
        )

    def start(self) -> None:
        self._poll_task = asyncio.create_task(self._poll_loop())

    def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()

    def _observe_depth(self, options: CallbackOptions) -> list[Observation]:
        return [Observation(self._depth_by_state.get(state, 0), {"state": state}) for state in self._STATES]

    def _observe_worker_count(self, options: CallbackOptions) -> list[Observation]:
        return [Observation(self._worker_count)]

    async def _poll_loop(self) -> None:
        while True:
            try:
                for state in self._STATES:
                    self._depth_by_state[state] = await self._queue.count(state)
                queue_info = await self._queue.info()
                self._worker_count = len(queue_info["workers"])
            except Exception as error:
                logger.warning("SAQ queue metrics poll failed (error={error})", error=error)
            await asyncio.sleep(self._poll_interval)
