from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from open_telemetry_experiment_worker.dependencies import EnqueueServiceDep
from open_telemetry_experiment_worker.schemas import JobRequest, JobResponse
from open_telemetry_experiment_worker.services import EnqueueError

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, tags=["Jobs"])
async def create_job(request: JobRequest, service: EnqueueServiceDep) -> JobResponse:
    try:
        job_id = await service.enqueue(request.request_id, request.text, request.callback_url)
    except EnqueueError as error:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to enqueue job") from error
    return JobResponse(job_id=job_id)
