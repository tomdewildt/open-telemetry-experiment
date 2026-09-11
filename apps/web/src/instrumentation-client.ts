import { W3CTraceContextPropagator } from "@opentelemetry/core";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";
import { resourceFromAttributes } from "@opentelemetry/resources";
import {
  BatchSpanProcessor,
  ParentBasedSampler,
  StackContextManager,
  TraceIdRatioBasedSampler,
  WebTracerProvider,
} from "@opentelemetry/sdk-trace-web";

if (process.env.NEXT_PUBLIC_WEB_OTEL_ENABLED === "true") {
  const endpoint = process.env.NEXT_PUBLIC_WEB_OTEL_ENDPOINT ?? "http://localhost:4318";
  const sampleRatio = Number(process.env.NEXT_PUBLIC_WEB_OTEL_SAMPLE_RATIO ?? "1");
  const environment = process.env.NEXT_PUBLIC_WEB_ENV ?? "dev";

  const provider = new WebTracerProvider({
    resource: resourceFromAttributes({
      "service.name": "@opentelemetry/web-browser",
      "deployment.environment": environment,
    }),
    sampler: new ParentBasedSampler({ root: new TraceIdRatioBasedSampler(sampleRatio) }),
    spanProcessors: [new BatchSpanProcessor(new OTLPTraceExporter({ url: `${endpoint}/v1/traces` }))],
  });

  // StackContextManager keeps the active span through synchronous calls (enough to parent a fetch under a
  // click span); the browser has no AsyncLocalStorage equivalent.
  provider.register({
    contextManager: new StackContextManager(),
    propagator: new W3CTraceContextPropagator(),
  });

  registerInstrumentations({
    tracerProvider: provider,
    instrumentations: [
      // Same-origin fetches get a traceparent header automatically, so /api/submit continues into the server
      // trace. The status poll is dropped to keep traces about real user actions.
      new FetchInstrumentation({ ignoreUrls: [/\/api\/requests$/] }),
    ],
  });
}
