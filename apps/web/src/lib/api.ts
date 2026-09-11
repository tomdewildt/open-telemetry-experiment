import { getLogger } from "@/logging";
import { NextResponse } from "next/server";
import { z } from "zod";

const logger = getLogger("app.api");

type Handler = (request: Request) => Promise<Response> | Response;

// Normalizes thrown errors into JSON responses.
export function withApi(handler: Handler) {
  return async (request: Request): Promise<Response> => {
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
      return NextResponse.json({ message: "Internal server error" }, { status: 500 });
    }
  };
}
