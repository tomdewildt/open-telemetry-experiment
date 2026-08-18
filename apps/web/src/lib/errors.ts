export class HttpError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export class ValidationError extends Error {
  constructor(readonly errors: Record<string, string[]>) {
    super("Validation error");
  }
}
