export interface Statement {
  bind(...values: unknown[]): Statement;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  all<T = Record<string, unknown>>(): Promise<{results: T[]}>;
  run(): Promise<{meta: {changes: number}}>;
}
export interface Database { prepare(sql: string): Statement; batch(statements: Statement[]): Promise<unknown[]>; }
export type Env = {
  DB?: Database; ASSETS?: {fetch(request: Request): Promise<Response>};
  SOLANA_RPC_URL?: string; HELIUS_API_KEY?: string; BIRDEYE_API_KEY?: string;
  COINGECKO_DEMO_API_KEY?: string; APP_ORIGIN?: string;
};
export class ApiError extends Error { constructor(public status: number, message: string) {super(message);} }
export const WSOL = "So11111111111111111111111111111111111111112";
export const BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
export function decode58(s: string): Uint8Array {
  if (!s || s.length > 90) throw new ApiError(422, "Invalid base58 value.");
  let value = 0n;
  for (const char of s) {const digit = BASE58.indexOf(char); if (digit < 0) throw new ApiError(422, "Invalid Solana address."); value = value * 58n + BigInt(digit);}
  const bytes: number[] = [];
  while (value) {bytes.push(Number(value & 255n)); value >>= 8n;}
  for (const char of s) {if (char !== "1") break; bytes.push(0);}
  return Uint8Array.from(bytes.reverse());
}
export function address(s: string): string {if (decode58(s).length !== 32) throw new ApiError(422, "Enter a valid 32-byte Solana public address."); return s;}
export function signature(s: string): string {if (decode58(s).length !== 64) throw new ApiError(422, "Invalid transaction signature."); return s;}
export const finite = (v: unknown): number | null => !["number", "string"].includes(typeof v) || (typeof v === "string" && !v.trim()) || !Number.isFinite(Number(v)) ? null : Number(v);
export const timestamp = () => Math.floor(Date.now() / 1000);
export const retrieved = () => new Date().toISOString();
export function requiredDB(env: Env): Database {if (!env.DB) throw new ApiError(503, "Persistent storage is unavailable. Please retry later."); return env.DB;}
export async function jsonBody(request: Request): Promise<Record<string, unknown>> {
  const text = await request.text(); if (text.length > 65536) throw new ApiError(413, "Request is too large.");
  try {const value = JSON.parse(text); if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(); return value;}
  catch {throw new ApiError(422, "Invalid JSON request.");}
}
type Cached = {expires: number; value: unknown};
const cached = new Map<string, Cached>(), flights = new Map<string, Promise<unknown>>();
export async function remember<T>(key: string, ttl: number, work: () => Promise<T>): Promise<T> {
  const hit = cached.get(key); if (hit && hit.expires > Date.now()) return hit.value as T;
  if (flights.has(key)) return flights.get(key) as Promise<T>;
  const promise = work().then(value => {if (cached.size >= 256) cached.delete(cached.keys().next().value!); cached.set(key, {expires: Date.now() + ttl * 1000, value}); return value;}).finally(() => flights.delete(key));
  flights.set(key, promise); return promise;
}
export async function upstream(url: string, init: RequestInit = {}, label = "Data provider"): Promise<any> {
  for (let attempt = 0; attempt < 2; attempt++) {
    let response: Response;
    try {response = await fetch(url, {...init, signal: AbortSignal.timeout(10000)});}
    catch {if (attempt === 0) continue; throw new ApiError(503, `${label} did not respond. Retry shortly; no demo data was substituted.`);}
    if (response.status === 429 || response.status >= 500) {
      if (attempt === 0) {await new Promise(resolve => setTimeout(resolve, Math.min(Number(response.headers.get("Retry-After") || 1), 2) * 1000)); continue;}
      throw new ApiError(response.status === 429 ? 429 : 503, `${label} ${response.status === 429 ? "rate limit reached" : "is temporarily unavailable"}. Retry shortly.`);
    }
    if (!response.ok) throw new ApiError(503, `${label} rejected the request (HTTP ${response.status}). Check provider access or API plan.`);
    try {return await response.json();} catch {throw new ApiError(502, `${label} returned an invalid response.`);}
  }
  throw new ApiError(503, `${label} is unavailable.`);
}
