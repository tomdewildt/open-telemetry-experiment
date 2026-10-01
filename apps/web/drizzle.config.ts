import { defineConfig } from "drizzle-kit";

function getEnvironmentVariable(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./migrations",
  dialect: "postgresql",
  dbCredentials: {
    url:
      `postgres://${encodeURIComponent(getEnvironmentVariable("WEB_POSTGRES_USER"))}:` +
      `${encodeURIComponent(getEnvironmentVariable("WEB_POSTGRES_PASSWORD"))}@` +
      `${getEnvironmentVariable("WEB_POSTGRES_HOST")}:${getEnvironmentVariable("WEB_POSTGRES_PORT")}/${getEnvironmentVariable("WEB_POSTGRES_DB")}`,
  },
});
