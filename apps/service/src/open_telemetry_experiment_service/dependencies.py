from typing import Annotated

from fastapi import Depends

from open_telemetry_experiment_service.services import ProcessService


def get_process_service() -> ProcessService:
    return ProcessService()


ProcessServiceDep = Annotated[ProcessService, Depends(get_process_service)]
