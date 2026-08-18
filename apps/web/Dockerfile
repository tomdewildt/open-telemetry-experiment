# Dependencies
FROM oven/bun:1 AS deps
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Dev
FROM deps AS dev
COPY . .
EXPOSE 3000
CMD ["sh", "-c", "bunx drizzle-kit push && bun run dev"]

# Builder
FROM deps AS builder
COPY . .
RUN bun run build

# Runner
FROM oven/bun:1 AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Isolated migration toolchain
WORKDIR /app/migrate
COPY --from=builder /app/drizzle.config.ts ./drizzle.config.ts
COPY --from=builder /app/src/db ./src/db
RUN bun add drizzle-kit drizzle-orm postgres

WORKDIR /app
EXPOSE 3000

CMD ["sh", "-c", "cd /app/migrate && bunx drizzle-kit push && cd /app && bun server.js"]
