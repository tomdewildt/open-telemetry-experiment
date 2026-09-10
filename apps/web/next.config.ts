import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  serverExternalPackages: [
    "pino",
    "@vercel/otel",
    "@opentelemetry/sdk-logs",
    "@opentelemetry/exporter-logs-otlp-proto",
    "@opentelemetry/instrumentation-pino",
  ],
  logging: {
    incomingRequests: false,
  },
};

export default nextConfig;
