import { NextResponse } from "next/server";
import { HttpError, ValidationError } from "@/lib/errors";
import { getLogger, requestContext } from "@/logging";

const logger = getLogger("app.api");

type Handler = (request: Request) => Promise<Response> | Response;

// Access logging is handled globally by initAccessLog (node http hook); this
// wrapper only binds the request-id context (for app logs) and normalizes errors.
export function withApi(handler: Handler) {
  return async (request: Request): Promise<Response> => {
    const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();

    return requestContext.run({ requestId }, async () => {
      try {
        return await handler(request);
      } catch (error) {
        const { status, body } = toErrorResponse(error);
        if (status >= 500) {
          logger.error({ err: error }, "Unhandled error");
        }
        return NextResponse.json(body, { status });
      }
    });
  };
}

function toErrorResponse(error: unknown): { status: number; body: Record<string, unknown> } {
  if (error instanceof ValidationError) {
    return { status: 422, body: { message: error.message, errors: error.errors } };
  }
  if (error instanceof HttpError) {
    return { status: error.status, body: { message: error.message } };
  }
  return { status: 500, body: { message: "Internal server error" } };
}
