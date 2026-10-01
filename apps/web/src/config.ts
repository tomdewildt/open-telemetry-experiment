import { parseRate } from "@/lib/failure";

export type Environment = "dev" | "prod";

function getEnvironmentVariable(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    // `next build` evaluates modules without the runtime env. Validate at runtime only, not during the build.
    if (process.env.NEXT_PHASE === "phase-production-build") {
      return "";
    }
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function getPostgresUrl(
  user: string,
  password: string,
  host: string,
  port: string,
  database: string,
): string {
  return `postgres://${encodeURIComponent(user)}:${encodeURIComponent(password)}@${host}:${port}/${database}`;
}

export const config = {
  ENV: (process.env.WEB_ENV as Environment) ?? "prod",
  LOG_LEVEL: process.env.WEB_LOG_LEVEL ?? "info",

  TITLE: "OpenTelemetry Experiment Web",
  DESCRIPTION:
    "Accepts text, enqueues work via the worker api, and shows the results.",
  VERSION: process.env.WEB_VERSION ?? "dev",

  // A valid placeholder during the build (the DB client is constructed at import but never queried then).
  DATABASE_URL:
    process.env.NEXT_PHASE === "phase-production-build"
      ? "postgres://build:build@localhost:5432/build"
      : getPostgresUrl(
          getEnvironmentVariable("WEB_POSTGRES_USER"),
          getEnvironmentVariable("WEB_POSTGRES_PASSWORD"),
          getEnvironmentVariable("WEB_POSTGRES_HOST"),
          getEnvironmentVariable("WEB_POSTGRES_PORT"),
          getEnvironmentVariable("WEB_POSTGRES_DB"),
        ),
  WORKER_API_BASE_URL: getEnvironmentVariable("WEB_WORKER_API_BASE_URL"),
  BASE_URL: getEnvironmentVariable("WEB_BASE_URL"),

  SERVER_FAILURE_RATE: parseRate(process.env.WEB_SERVER_FAILURE_RATE, 0.1),

  OTEL_ENABLED: process.env.WEB_OTEL_ENABLED === "true",
  OTEL_ENDPOINT:
    process.env.WEB_OTEL_ENABLED === "true"
      ? getEnvironmentVariable("WEB_OTEL_ENDPOINT")
      : (process.env.WEB_OTEL_ENDPOINT ?? ""),
  OTEL_SERVICE_NAMESPACE:
    process.env.WEB_OTEL_SERVICE_NAMESPACE ?? "opentelemetry",
  OTEL_SERVICE_NAME: process.env.WEB_OTEL_SERVICE_NAME ?? "web-server",
  OTEL_SAMPLE_RATIO: parseRate(process.env.WEB_OTEL_SAMPLE_RATIO, 1.0),
} as const;
