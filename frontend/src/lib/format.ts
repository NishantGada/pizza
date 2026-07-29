const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function money(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  return usd.format(Number.isFinite(n) ? n : 0);
}

/** "0.6000" -> "60%" */
export function percent(value: string | number, digits = 0): string {
  const n = typeof value === "string" ? Number(value) : value;
  return `${(n * 100).toFixed(digits)}%`;
}

/** ISO date "2026-07-01" -> "Jul 1" */
export function shortDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

export function dateRange(start: string, end: string): string {
  return `${shortDate(start)} – ${shortDate(end)}`;
}
