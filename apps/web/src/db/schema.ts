import { pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

export const requests = pgTable("requests", {
  id: serial("id").primaryKey(),
  requestId: text("request_id").notNull().unique(),
  text: text("text").notNull(),
  status: text("status").notNull().default("pending"),
  result: text("result"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
