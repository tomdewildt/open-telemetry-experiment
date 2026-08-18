from collections import defaultdict
from enum import StrEnum, auto

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR

from open_telemetry_experiment_service.config import config


class ConfigRead(BaseModel):
    title: str
    description: str
    version: str
    env: str


class HealthStatus(StrEnum):
    HEALTHY = auto()
    UNHEALTHY = auto()


class HealthRead(BaseModel):
    status: HealthStatus


def config_handler(response: Response) -> ConfigRead:
    response.status_code = HTTP_200_OK
    return ConfigRead(title=config.TITLE, description=config.DESCRIPTION, version=config.VERSION, env=config.ENV)


def health_handler(response: Response) -> HealthRead:
    response.status_code = HTTP_200_OK
    return HealthRead(status=HealthStatus.HEALTHY)


def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"message": exc.detail}, status_code=exc.status_code, headers=exc.headers)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"message": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)


def validation_exception_handler(_: Request, exc: RequestValidationError | ResponseValidationError) -> JSONResponse:
    errors = defaultdict(list)
    for error in exc.errors():
        loc, msg = error["loc"], error["msg"]
        loc = [location for location in loc if isinstance(location, str)]
        errors[".".join(loc)].append(msg)
    return JSONResponse({"message": "Validation error", "errors": errors}, status_code=HTTP_422_UNPROCESSABLE_CONTENT)
