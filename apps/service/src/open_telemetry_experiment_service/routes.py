from fastapi import APIRouter, HTTPException
from opentelemetry import trace
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
        # Record on the request span so the handled failure still shows in the Exceptions view.
        trace.get_current_span().record_exception(error)
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail="Processing failed") from error
