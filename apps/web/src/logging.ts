import { config } from "@/config";
import { AsyncLocalStorage } from "node:async_hooks";
import http from "node:http";
import { Writable } from "node:stream";
import { format } from "node:util";
import pino from "pino";

export const requestContext = new AsyncLocalStorage<{ requestId: string }>();

const LEVEL_NAMES: Record<string, string> = {
  trace: "TRACE",
  debug: "DEBUG",
  info: "INFO",
  warn: "WARNING",
  error: "ERROR",
  fatal: "CRITICAL",
};

const LEVEL_COLORS: Record<string, string> = {
  trace: "\x1b[36m",
  debug: "\x1b[34m",
  info: "\x1b[32m",
  warn: "\x1b[33m",
  error: "\x1b[31m",
  fatal: "\x1b[41m",
};

const GREEN = "\x1b[32m";
const CYAN = "\x1b[36m";
const BLUE = "\x1b[34m";
const RESET = "\x1b[0m";

function formatTime(epochMs: number): string {
  const date = new Date(epochMs);
  const pad = (value: number, width = 2) => String(value).padStart(width, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}`
  );
}

const prettyStream = new Writable({
  write(chunk, _encoding, callback) {
    let record: Record<string, unknown>;
    try {
      record = JSON.parse(chunk.toString());
    } catch {
      process.stdout.write(chunk);
      callback();
      return;
    }

    const level = record.level as string;
    const color = LEVEL_COLORS[level] ?? "";
    const levelName = (LEVEL_NAMES[level] ?? level.toUpperCase()).padEnd(8);
    const time = formatTime(record.time as number);
    const name = (record.name as string) ?? "-";
    const correlationId = record.correlation_id as string | undefined;
    const cid = correlationId ? ` | ${BLUE}[${correlationId}]${RESET}` : "";
    const stack = (record.err as { stack?: string } | undefined)?.stack;

    let line = `${GREEN}${time}${RESET} | ${color}${levelName}${RESET} | ${CYAN}${name}${RESET}${cid} - ${color}${record.msg}${RESET}\n`;
    if (stack) line += `${stack}\n`;

    process.stdout.write(line);
    callback();
  },
});

export const logger = pino(
  {
    level: config.LOG_LEVEL,
    base: undefined,
    formatters: {
      level: (label) => ({ level: label }),
    },
    serializers: { err: pino.stdSerializers.err },
    mixin() {
      const store = requestContext.getStore();
      return store ? { correlation_id: store.requestId } : {};
    },
  },
  config.ENV === "dev" ? prettyStream : process.stdout,
);

export function getLogger(name: string) {
  return logger.child({ name });
}

export function getRequestId(): string | undefined {
  return requestContext.getStore()?.requestId;
}

// Patch node's http server to log every request on finish, which is the only place in Next.js that sees
// the final status + duration.
let accessLogInitialized = false;

export function initAccessLog(): void {
  if (accessLogInitialized) return;
  accessLogInitialized = true;

  const accessLogger = getLogger("app.access");
  const proto = http.Server.prototype as unknown as {
    emit: (event: string, ...args: unknown[]) => boolean;
  };
  const originalEmit = proto.emit;

  proto.emit = function (
    this: unknown,
    event: string,
    ...args: unknown[]
  ): boolean {
    if (event === "request") {
      const req = args[0] as http.IncomingMessage;
      const res = args[1] as http.ServerResponse;
      const start = performance.now();
      res.on("finish", () => {
        const url = req.url ?? "";
        if (url.startsWith("/_next/") || url === "/favicon.ico") return;
        const correlationId = res.getHeader("x-request-id");
        const duration = Math.round(performance.now() - start);
        accessLogger.info(
          {
            correlation_id:
              typeof correlationId === "string" ? correlationId : undefined,
            method: req.method,
            path: url,
            status: res.statusCode,
            duration,
          },
          `${req.method} ${url} ${res.statusCode} (${duration}ms)`,
        );
      });
    }
    return originalEmit.apply(this, [event, ...args]);
  };
}

// Route console.* (used by next.js dev logger and any library) through pino.
export function initLogging(): void {
  const target = logger.child({ name: "console" });
  const levels = {
    log: "info",
    info: "info",
    warn: "warn",
    error: "error",
    debug: "debug",
    trace: "trace",
  } as const;

  for (const method of Object.keys(levels) as (keyof typeof levels)[]) {
    const level = levels[method];
    console[method] = (...args: unknown[]) => {
      const message = format(...args);
      if (message.trim()) target[level](message);
    };
  }
}
