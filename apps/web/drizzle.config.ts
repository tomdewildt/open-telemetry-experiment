import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./migrations",
  dialect: "postgresql",
  dbCredentials: {
    url:
      process.env.WEB_DATABASE_URL ??
      "postgres://postgres:postgres@localhost:5432/postgres",
  },
});
