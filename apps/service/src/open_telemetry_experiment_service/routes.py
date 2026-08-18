from fastapi import APIRouter

from open_telemetry_experiment_service.dependencies import ProcessServiceDep
from open_telemetry_experiment_service.schemas import ProcessRequest, ProcessResponse

router = APIRouter()


@router.post("/process", response_model=ProcessResponse, tags=["Process"])
async def process(request: ProcessRequest, service: ProcessServiceDep) -> ProcessResponse:
    return await service.process(request.text)
