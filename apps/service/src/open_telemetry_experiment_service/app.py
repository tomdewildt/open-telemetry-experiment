from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware

from open_telemetry_experiment_service.config import Environment, config
from open_telemetry_experiment_service.logging import init_logging
from open_telemetry_experiment_service.middleware import AccessLogMiddleware
from open_telemetry_experiment_service.routes import router
from open_telemetry_experiment_service.utils import (
    config_handler,
    health_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


def create_app() -> FastAPI:
    # Setup logging
    init_logging(config.ENV, config.LOG_LEVEL)

    # Define app
    app = FastAPI(
        title=config.TITLE,
        description=config.DESCRIPTION,
        version=config.VERSION,
        openapi_url="/spec.json" if config.ENV in [Environment.DEV] else None,
        docs_url="/" if config.ENV in [Environment.DEV] else None,
        redoc_url=None,
        debug=config.ENV in [Environment.DEV],
    )

    # Define middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ALLOW_ORIGINS,
        allow_methods=config.CORS_ALLOW_METHODS,
        allow_headers=config.CORS_ALLOW_HEADERS,
        expose_headers=config.CORS_EXPOSE_HEADERS,
    )
    app.add_middleware(AccessLogMiddleware)

    # Define exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(ResponseValidationError, validation_exception_handler)  # type: ignore

    # Define common routes
    app.add_api_route("/config", config_handler, name="generic:config", methods=["GET"], tags=["Generic"])
    app.add_api_route("/health", health_handler, name="generic:health", methods=["GET"], tags=["Generic"])

    # Define api routes
    api = APIRouter(prefix="/api/v1")
    api.include_router(router)
    app.include_router(api)

    return app
