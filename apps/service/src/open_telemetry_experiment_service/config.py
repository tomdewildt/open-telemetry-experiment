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


class ServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERVICE_", env_file=".env", env_file_encoding="utf-8")

    ENV: Environment = Environment.PROD
    LOG_LEVEL: LogLevel = LogLevel.INFO

    TITLE: str = "OpenTelemetry Experiment Service"
    DESCRIPTION: str = "Processes requests locally and fails intermittently."

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

    FAILURE_RATE: float = 0.3

    OTEL_ENABLED: bool = False
    OTEL_ENDPOINT: str = "http://host.docker.internal:4318"
    OTEL_SERVICE_NAMESPACE: str = "opentelemetry"
    OTEL_SERVICE_NAME: str = "service"
    OTEL_SAMPLE_RATIO: float = 1.0


config = ServiceConfig()
