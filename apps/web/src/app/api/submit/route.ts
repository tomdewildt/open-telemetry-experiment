import { eq } from "drizzle-orm";
import { NextResponse } from "next/server";
import { config } from "@/config";
import { db } from "@/db";
import { requests } from "@/db/schema";
import { withApi } from "@/lib/api";
import { shouldFail } from "@/lib/failure";
import { submitSchema } from "@/lib/schemas";
import { getLogger, getRequestId } from "@/logging";

const logger = getLogger("app.api.submit");

export const POST = withApi(async (request) => {
  if (shouldFail(config.SERVER_FAILURE_RATE)) {
    return NextResponse.json({ message: "injected failure" }, { status: 500 });
  }

  const { text } = submitSchema.parse(await request.json());
  const requestId = crypto.randomUUID();
  const correlationId = getRequestId();

  await db.insert(requests).values({ requestId, text });

  try {
    const response = await fetch(`${config.WORKER_API_BASE_URL}/jobs`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(correlationId ? { "x-request-id": correlationId } : {}),
      },
      body: JSON.stringify({
        request_id: requestId,
        text,
        callback_url: `${config.BASE_URL}/api/callback`,
      }),
    });
    if (!response.ok) {
      throw new Error(`worker-api responded with ${response.status}`);
    }
  } catch (error) {
    logger.error({ err: error }, "Enqueue failed");
    await db
      .update(requests)
      .set({ status: "failed", result: String(error) })
      .where(eq(requests.requestId, requestId));
    return NextResponse.json({ request_id: requestId, status: "failed" });
  }

  return NextResponse.json({ request_id: requestId });
});
