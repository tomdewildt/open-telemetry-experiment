import { NextResponse } from "next/server";
import { client } from "@/db";
import { withApi } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = withApi(async () => {
  await client`SELECT 1`;
  return NextResponse.json({ status: "healthy" });
});
