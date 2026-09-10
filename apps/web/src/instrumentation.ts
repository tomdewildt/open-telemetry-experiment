export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { config } = await import("@/config");
    if (config.OTEL_ENABLED) {
      const { registerOTel, OTLPHttpProtoTraceExporter } = await import("@vercel/otel");
      const { BatchLogRecordProcessor } = await import("@opentelemetry/sdk-logs");
      const { OTLPLogExporter } = await import("@opentelemetry/exporter-logs-otlp-proto");
      const { PinoInstrumentation } = await import("@opentelemetry/instrumentation-pino");

      process.env.OTEL_TRACES_SAMPLER_ARG ??= String(config.OTEL_SAMPLE_RATIO);
      registerOTel({
        serviceName: `@${config.OTEL_SERVICE_NAMESPACE}/${config.OTEL_SERVICE_NAME}`,
        attributes: {
          "service.version": config.VERSION,
          "deployment.environment": config.ENV,
        },
        traceSampler: "parentbased_traceidratio",
        traceExporter: new OTLPHttpProtoTraceExporter({ url: `${config.OTEL_ENDPOINT}/v1/traces` }),
        logRecordProcessors: [
          new BatchLogRecordProcessor({ exporter: new OTLPLogExporter({ url: `${config.OTEL_ENDPOINT}/v1/logs` }) }),
        ],
        // Bridge pino logs to OTLP (the analogue of the Python loguru -> OTLP handler).
        instrumentations: ["fetch", new PinoInstrumentation()],
        // @vercel/otel only propagates trace context to matched URLs, so opt the worker api in
        // or the web -> worker-api hop stays a separate trace.
        instrumentationConfig: {
          fetch: { propagateContextUrls: [config.WORKER_API_BASE_URL] },
        },
      });
    }

    const { initLogging, initAccessLog } = await import("@/logging");
    initLogging();
    initAccessLog();
  }
}
