import { eq } from "drizzle-orm";
import { NextResponse } from "next/server";
import { db } from "@/db";
import { requests } from "@/db/schema";
import { withApi } from "@/lib/api";
import { callbackSchema } from "@/lib/schemas";

export const POST = withApi(async (request) => {
  const { request_id, status, result, error } = callbackSchema.parse(await request.json());

  await db
    .update(requests)
    .set({ status, result: result ?? error ?? null })
    .where(eq(requests.requestId, request_id));

  return NextResponse.json({ ok: true });
});
