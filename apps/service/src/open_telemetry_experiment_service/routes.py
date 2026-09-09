from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from open_telemetry_experiment_service.dependencies import ProcessServiceDep
from open_telemetry_experiment_service.schemas import ProcessRequest, ProcessResponse
from open_telemetry_experiment_service.services import ProcessingError

router = APIRouter()


@router.post("/process", response_model=ProcessResponse, tags=["Process"])
async def process(request: ProcessRequest, service: ProcessServiceDep) -> ProcessResponse:
    try:
        return await service.process(request.text)
    except ProcessingError as error:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail="Processing failed") from error
