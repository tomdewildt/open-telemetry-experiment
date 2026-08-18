from collections.abc import Sequence
from enum import StrEnum

from pydantic import computed_field
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
    CORS_ALLOW_HEADERS: Sequence[str] = ("X-Requested-With", "X-Request-ID")
    CORS_EXPOSE_HEADERS: Sequence[str] = ("X-Request-ID",)

    REDIS_URL: str = "redis://redis:6379"

    SERVICE_BASE_URL: str = "http://service:8000/api/v1"

    EXTERNAL_API_BASE_URL: str = "https://uselessfacts.jsph.pl/api/v2"

    API_FAILURE_RATE: float = 0.1
    WORKER_FAILURE_RATE: float = 0.1


config = WorkerConfig()
