import {ApiError, finite} from "./runtime";

function records(data: unknown): Record<string, unknown>[] {
  if (!Array.isArray(data) || data.some(row => !row || typeof row !== "object" || Array.isArray(row))) {
    throw new ApiError(502, "Historical provider returned invalid observations.");
  }
  return data;
}

function observedTime(value: unknown, first: number, last: number, resolution: number): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < first || value > last || value % resolution !== 0) {
    throw new ApiError(502, "Historical provider returned an invalid or out-of-window timestamp.");
  }
  return value;
}

export function researchPrices(items: unknown, start: number, end: number) {
  return records(items).map(row => {
    const ts = observedTime(row.unixTime, start, end, 300);
    const price = finite(row.value);
    if (price !== null && price <= 0) throw new ApiError(502, "Historical provider returned a non-positive token price.");
    return {ts: ts + 300, source_price_ts: ts, price_usd: price};
  });
}

export function researchLiquidity(items: unknown, anchor: number) {
  return records(items).map(row => {
    const ts = observedTime(row.unix_time, 1704067200, anchor, 60);
    const depth = finite(row.exit_liquidity_usd), total = finite(row.liquidity_usd);
    if ((depth !== null && depth < 0) || (total !== null && total < 0)) {
      throw new ApiError(502, "Historical provider returned negative liquidity.");
    }
    return {ts, liquidity_usd: depth, total_liquidity_usd: total};
  });
}
