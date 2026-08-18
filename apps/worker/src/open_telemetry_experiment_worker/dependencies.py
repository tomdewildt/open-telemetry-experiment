from typing import Annotated

from fastapi import Depends

from open_telemetry_experiment_worker.queue import queue
from open_telemetry_experiment_worker.services import EnqueueService


def get_enqueue_service() -> EnqueueService:
    return EnqueueService(queue)


EnqueueServiceDep = Annotated[EnqueueService, Depends(get_enqueue_service)]
