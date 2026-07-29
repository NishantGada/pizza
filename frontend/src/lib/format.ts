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

export type Kind = "PERCENT" | "FIXED";

/** Stored value (fraction for percent, dollars for fixed) -> form input string. */
export function kindToInput(kind: Kind, value: string | number): string {
  return kind === "PERCENT" ? String(Number(value) * 100) : String(value);
}
/** Form input string -> stored value for the given kind. */
export function kindToStored(kind: Kind, input: string | number): string {
  return kind === "PERCENT" ? String(Number(input) / 100) : String(input);
}
/** Human label for a stored kind/value pair: "5%" or "$50.00". */
export function describeKind(kind: Kind, value: string | number): string {
  return kind === "PERCENT" ? percent(value) : money(value);
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
