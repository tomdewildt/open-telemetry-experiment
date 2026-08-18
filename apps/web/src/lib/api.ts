import { getLogger, requestContext } from "@/logging";
import { NextResponse } from "next/server";
import { z } from "zod";

const logger = getLogger("app.api");

type Handler = (request: Request) => Promise<Response> | Response;

// Binds the request-id context (for in-handler logs) and normalizes thrown errors.
export function withApi(handler: Handler) {
  return async (request: Request): Promise<Response> => {
    const requestId =
      request.headers.get("x-request-id") ?? crypto.randomUUID();

    return requestContext.run({ requestId }, async () => {
      try {
        return await handler(request);
      } catch (error) {
        if (error instanceof z.ZodError) {
          return NextResponse.json(
            {
              message: "Validation error",
              errors: z.flattenError(error).fieldErrors,
            },
            { status: 422 },
          );
        }
        logger.error({ err: error }, "Unhandled error");
        return NextResponse.json(
          { message: "Internal server error" },
          { status: 500 },
        );
      }
    });
  };
}
