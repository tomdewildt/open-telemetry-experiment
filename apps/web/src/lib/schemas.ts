import { z } from "zod";
import { ValidationError } from "@/lib/errors";

export const submitSchema = z.object({
  text: z.string().min(1),
});

export const callbackSchema = z.object({
  request_id: z.string().min(1),
  status: z.string().min(1),
  result: z.string().nullish(),
  error: z.string().nullish(),
});

export function validate<T>(schema: z.ZodType<T>, data: unknown): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    const errors: Record<string, string[]> = {};
    for (const issue of result.error.issues) {
      const key = issue.path.join(".") || "_";
      (errors[key] ??= []).push(issue.message);
    }
    throw new ValidationError(errors);
  }
  return result.data;
}
