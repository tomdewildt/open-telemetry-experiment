from collections.abc import Sequence
from enum import StrEnum

from pydantic import ValidationInfo, computed_field, field_validator
from pydantic_core import PydanticCustomError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEV = "dev"
    PROD = "prod"


class LogLevel(StrEnum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class WorkerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKER_", env_file=".env", env_file_encoding="utf-8")

    ENV: Environment = Environment.PROD
    LOG_LEVEL: LogLevel = LogLevel.INFO

    TITLE: str = "OpenTelemetry Experiment Worker"
    DESCRIPTION: str = "Enqueues jobs and processes them via the service and an external api."

    @computed_field
    @property
    def VERSION(self) -> str:  # noqa: N802
        try:
            with open("./VERSION", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError:
            return "dev"

    CORS_ALLOW_ORIGINS: Sequence[str] = ("*",)
    CORS_ALLOW_METHODS: Sequence[str] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    CORS_ALLOW_HEADERS: Sequence[str] = ("X-Requested-With",)
    CORS_EXPOSE_HEADERS: Sequence[str] = ()

    REDIS_HOST: str
    REDIS_PORT: int

    @computed_field
    @property
    def REDIS_URL(self) -> str:  # noqa: N802
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    SERVICE_BASE_URL: str

    EXTERNAL_API_BASE_URL: str

    API_FAILURE_RATE: float = 0.1
    WORKER_FAILURE_RATE: float = 0.1

    OTEL_ENABLED: bool = False
    OTEL_ENDPOINT: str = ""
    OTEL_SERVICE_NAMESPACE: str = "opentelemetry"
    OTEL_SERVICE_NAME: str = "worker"
    OTEL_SAMPLE_RATIO: float = 1.0

    @field_validator("OTEL_ENDPOINT", mode="after")
    @classmethod
    def _require_otel_endpoint(cls, value: str, info: ValidationInfo) -> str:
        if info.data.get("OTEL_ENABLED") and not value:
            raise PydanticCustomError("missing", "Field required")
        return value


config = WorkerConfig()  # pyright: ignore[reportCallIssue]
