import { z } from "zod";

export const submitSchema = z.object({
  text: z.string().min(1),
});

export const callbackSchema = z.object({
  request_id: z.string().min(1),
  status: z.string().min(1),
  result: z.string().nullish(),
  error: z.string().nullish(),
});
