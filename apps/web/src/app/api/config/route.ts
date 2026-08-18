import { NextResponse } from "next/server";
import { config } from "@/config";
import { withApi } from "@/lib/api";

export const GET = withApi(async () => {
  return NextResponse.json({
    title: config.TITLE,
    description: config.DESCRIPTION,
    version: config.VERSION,
    env: config.ENV,
  });
});
