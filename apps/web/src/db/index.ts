import { config } from "@/config";
import { instrumentDrizzleClient } from "@kubiks/otel-drizzle";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const client = postgres(config.DATABASE_URL);

export const db = drizzle(client, { schema });
if (config.OTEL_ENABLED) {
  instrumentDrizzleClient(db, { dbSystem: "postgresql" });
}

export { client };
