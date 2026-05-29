/**
 * Display helpers. Money/quantity values arrive as exact decimal strings; we format for
 * display only and never use the parsed number for posting math (the backend is authoritative).
 */

export function formatMoney(amount: string | null | undefined, currency = "USD"): string {
  if (amount == null || amount === "") return "—";
  const n = Number(amount);
  if (Number.isNaN(n)) return amount;
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(n);
  } catch {
    // Unknown ISO currency code — fall back to a plain 2-dp number with the code suffix.
    return `${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
  }
}

export function formatQuantity(value: string | null | undefined): string {
  if (value == null || value === "") return "—";
  const n = Number(value);
  return Number.isNaN(n) ? value : n.toLocaleString("en-US");
}

/** Signed delta with a leading +/- for display (e.g. price/quantity deltas). */
export function formatSignedNumber(value: string | null | undefined): string {
  if (value == null || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  const formatted = Math.abs(n).toLocaleString("en-US", { maximumFractionDigits: 4 });
  return n > 0 ? `+${formatted}` : n < 0 ? `-${formatted}` : "0";
}

export function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString("en-US");
}
