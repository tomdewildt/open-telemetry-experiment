import { desc } from "drizzle-orm";
import { NextResponse } from "next/server";
import { db } from "@/db";
import { requests } from "@/db/schema";
import { withApi } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = withApi(async () => {
  const rows = await db.select().from(requests).orderBy(desc(requests.createdAt)).limit(20);
  return NextResponse.json(rows);
});
