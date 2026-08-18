import { config } from "@/config";
import { AsyncLocalStorage } from "node:async_hooks";
import http from "node:http";
import { Writable } from "node:stream";
import { format } from "node:util";
import pino from "pino";

export const requestContext = new AsyncLocalStorage<{ requestId: string }>();

// Map pino's numeric levels onto the loguru level names used by the python apps.
const LEVEL_NAMES: Record<number, string> = {
  10: "TRACE",
  20: "DEBUG",
  30: "INFO",
  40: "WARNING",
  50: "ERROR",
  60: "CRITICAL",
};

const LEVEL_COLORS: Record<number, string> = {
  10: "\x1b[36m",
  20: "\x1b[34m",
  30: "\x1b[32m",
  40: "\x1b[33m",
  50: "\x1b[31m",
  60: "\x1b[41m",
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

    const level = record.level as number;
    const color = LEVEL_COLORS[level] ?? "";
    const levelName = (LEVEL_NAMES[level] ?? String(level)).padEnd(8);
    const time = formatTime(record.time as number);
    const name = (record.name as string) ?? "-";
    const requestId = record.requestId as string | undefined;
    const rid = requestId ? ` | ${BLUE}[${requestId}]${RESET}` : "";
    const stack = (record.err as { stack?: string } | undefined)?.stack;

    let line = `${GREEN}${time}${RESET} | ${color}${levelName}${RESET} | ${CYAN}${name}${RESET}${rid} - ${color}${record.msg}${RESET}\n`;
    if (stack) line += `${stack}\n`;

    process.stdout.write(line);
    callback();
  },
});

export const logger = pino(
  {
    level: config.LOG_LEVEL,
    base: undefined,
    serializers: { err: pino.stdSerializers.err },
    mixin() {
      const store = requestContext.getStore();
      return store ? { requestId: store.requestId } : {};
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

// Global access log: patch node's http server to log every request on finish,
// which is the only place in Next.js that sees the final status + duration.
let accessLogInitialized = false;

export function initAccessLog(): void {
  if (accessLogInitialized) return;
  accessLogInitialized = true;

  const accessLogger = getLogger("app.access");
  const proto = http.Server.prototype as unknown as { emit: (event: string, ...args: unknown[]) => boolean };
  const originalEmit = proto.emit;

  proto.emit = function (this: unknown, event: string, ...args: unknown[]): boolean {
    if (event === "request") {
      const req = args[0] as http.IncomingMessage;
      const res = args[1] as http.ServerResponse;
      const start = performance.now();
      res.on("finish", () => {
        const url = req.url ?? "";
        if (url.startsWith("/_next/") || url === "/favicon.ico") return;
        const requestId = res.getHeader("x-request-id");
        accessLogger.info(
          { requestId: typeof requestId === "string" ? requestId : undefined },
          `${req.method} ${url} ${res.statusCode} (${Math.round(performance.now() - start)}ms)`,
        );
      });
    }
    return originalEmit.apply(this, [event, ...args]);
  };
}

// Route console.* (used by Next's dev logger and any library) through pino,
// mirroring the python apps that funnel stdlib logging into loguru.
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
