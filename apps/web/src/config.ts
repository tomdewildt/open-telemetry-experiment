import { parseRate } from "@/lib/failure";

export type Environment = "dev" | "prod";

export const config = {
  ENV: (process.env.WEB_ENV as Environment) ?? "prod",
  LOG_LEVEL: process.env.WEB_LOG_LEVEL ?? "info",

  TITLE: "OpenTelemetry Experiment Web",
  DESCRIPTION: "Accepts text, enqueues work via the worker api, and shows the results.",
  VERSION: process.env.WEB_VERSION ?? "dev",

  DATABASE_URL: process.env.WEB_DATABASE_URL ?? "postgres://postgres:postgres@localhost:5432/postgres",
  WORKER_API_BASE_URL: process.env.WEB_WORKER_API_BASE_URL ?? "http://worker-api:8000/api/v1",
  BASE_URL: process.env.WEB_BASE_URL ?? "http://web:3000",

  SERVER_FAILURE_RATE: parseRate(process.env.WEB_SERVER_FAILURE_RATE, 0.1),

  OTEL_ENABLED: process.env.WEB_OTEL_ENABLED === "true",
  OTEL_ENDPOINT: process.env.WEB_OTEL_ENDPOINT ?? "http://host.docker.internal:4318",
  OTEL_SERVICE_NAMESPACE: process.env.WEB_OTEL_SERVICE_NAMESPACE ?? "opentelemetry",
  OTEL_SERVICE_NAME: process.env.WEB_OTEL_SERVICE_NAME ?? "web",
  OTEL_SAMPLE_RATIO: parseRate(process.env.WEB_OTEL_SAMPLE_RATIO, 1.0),
} as const;
