export function shouldFail(rate: number): boolean {
  return Math.random() < rate;
}

export function parseRate(raw: string | undefined, fallback: number): number {
  const rate = Number(raw);
  return Number.isFinite(rate) ? rate : fallback;
}
