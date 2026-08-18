from fastapi import APIRouter

from open_telemetry_experiment_worker.dependencies import EnqueueServiceDep
from open_telemetry_experiment_worker.schemas import JobRequest, JobResponse

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, tags=["Jobs"])
async def create_job(request: JobRequest, service: EnqueueServiceDep) -> JobResponse:
    job_id = await service.enqueue(request.request_id, request.text, request.callback_url)
    return JobResponse(job_id=job_id)
