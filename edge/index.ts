import {address, ApiError, Env, remember, requiredDB, retrieved, signature, timestamp, upstream} from "./runtime";
import {authRoute, originFor, requireWallet} from "./auth";
import {MarketDataService} from "./market";
import {SolanaService, WalletService} from "./solana";
import {researchPrices, researchLiquidity} from "./history";
import {experimentRoute} from "./experiments";
import {providerReadiness} from "./readiness";

function coverage(url: URL) {
  const start = Number(url.searchParams.get("start")), end = Number(url.searchParams.get("end"));
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1704067200 || end <= start || end - start > 14 * 86400 || end > timestamp()) throw new ApiError(422, "Choose a past historical window of at most 14 days, after 2024-01-01.");
  return {start, end};
}
async function routes(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url), path = url.pathname.replace(/\/$/, ""), method = request.method;
  if (path.startsWith("/api/experiments")) return experimentRoute(request, env, path);
  if (path.startsWith("/api/auth/")) return authRoute(request, env, path);
  if (path === "/api/providers/readiness" && method === "POST") {originFor(request, env); return Response.json(await providerReadiness(env));}
  if (path === "/api/live/status" && method === "GET") return Response.json({network: "mainnet-beta", kind: "REAL", rpc: true, rpc_provider: env.SOLANA_RPC_URL ? "configured RPC" : env.HELIUS_API_KEY ? "Helius" : "public Solana RPC", helius: Boolean(env.HELIUS_API_KEY), birdeye: Boolean(env.BIRDEYE_API_KEY), authentication: Boolean(env.DB), history_provider: env.BIRDEYE_API_KEY ? "Birdeye" : "CoinGecko / GeckoTerminal", engine: "shared Python browser worker"});
  if (path === "/api/markets/sol" && method === "GET") return Response.json(await new MarketDataService(env).sol());
  if (path === "/api/markets/search" && method === "GET") return Response.json(await new MarketDataService(env).search(url.searchParams.get("q") || ""));
  const tokenMatch = path.match(/^\/api\/markets\/([1-9A-HJ-NP-Za-km-z]+)(?:\/(history|research-prices|research-liquidity))?$/);
  if (tokenMatch && method === "GET") {
    const mint = address(tokenMatch[1]), action = tokenMatch[2], market = new MarketDataService(env);
    if (!action) return Response.json(await market.token(mint));
    if (action === "history") return Response.json(await market.history(mint, Number(url.searchParams.get("days") || 7)));
    if (!env.BIRDEYE_API_KEY) throw new ApiError(503, "BIRDEYE_API_KEY is required for historical research prices and liquidity. Display charts are never substituted for executable research data.");
    const headers = {"X-API-KEY": env.BIRDEYE_API_KEY, "x-chain": "solana"};
    if (action === "research-prices") {
      const {start, end} = coverage(url); if (end - start > 300 * 98) throw new ApiError(422, "Request price history in bounded chunks of at most 98 five-minute buckets.");
      const d = await remember(`bars:${mint}:${start}:${end}`, 3600, () => upstream(`https://public-api.birdeye.so/defi/history_price?address=${mint}&address_type=token&type=5m&time_from=${start}&time_to=${end}&ui_amount_mode=raw`, {headers}, "Birdeye research prices"));
      if (!d.success || d.data?.isScaledUiToken || !Array.isArray(d.data?.items)) throw new ApiError(503, "Historical token prices could not be normalized safely.");
      return Response.json({kind: "REAL", provider: "Birdeye", mint, retrieved_at: retrieved(), prices: researchPrices(d.data.items, start, end)});
    }
    const anchor = Number(url.searchParams.get("time"));
    if (!Number.isInteger(anchor) || anchor < 1704067200 || anchor > timestamp()) throw new ApiError(422, "Invalid historical liquidity timestamp.");
    const d = await remember(`liquidity:${mint}:${anchor}`, 3600, () => upstream(`https://public-api.birdeye.so/defi/v3/liquidity/history/token?address=${mint}&resolution=1m&time=${anchor}&direction=back&count=100`, {headers}, "Birdeye historical liquidity"));
    if (!d.success || !Array.isArray(d.data?.items)) throw new ApiError(503, "Historical liquidity is unavailable for this token or API plan.");
    const items = researchLiquidity(d.data.items, anchor);
    return Response.json({kind: "REAL", provider: "Birdeye", mint, retrieved_at: retrieved(), items, next_time: items.length ? Math.min(...items.map((p: any) => p.ts)) - 1 : null});
  }
  const walletMatch = path.match(/^\/api\/wallets\/([1-9A-HJ-NP-Za-km-z]+)(?:\/(transactions|observations|history))?$/);
  if (walletMatch) {
    const wallet = address(walletMatch[1]), action = walletMatch[2];
    if (!action && method === "GET") return Response.json(await new WalletService(env).snapshot(wallet));
    if (action === "transactions" && method === "GET") return Response.json(await new SolanaService(env).transactions(wallet, url.searchParams.get("before") || undefined));
    if (action === "observations" && method === "GET") {
      await requireWallet(request, env, wallet);
      const records = await requiredDB(env).prepare("SELECT ts, sol_balance, valued_usd, complete FROM wallet_snapshots WHERE wallet = ? ORDER BY ts DESC LIMIT 2000").bind(wallet).all();
      return Response.json({wallet, kind: "REAL", points: records.results.reverse(), limitations: ["Actual saved observations since login; past holdings are not reconstructed.", "Valued subtotal is partial where token quotes were missing at observation time."]});
    }
    if (action === "observations" && method === "POST") {
      originFor(request, env); await requireWallet(request, env, wallet);
      const data = await new WalletService(env).snapshot(wallet), now = Math.floor(new Date(data.retrieved_at).getTime() / 1000), id = wallet + ":" + Math.floor(now / 60);
      await requiredDB(env).batch([
        requiredDB(env).prepare("INSERT INTO wallet_snapshots (id, wallet, ts, sol_balance, valued_usd, complete, payload) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING").bind(id, wallet, now, data.sol_balance, data.valued_subtotal_usd, data.portfolio_complete ? 1 : 0, JSON.stringify(data)),
        requiredDB(env).prepare("DELETE FROM wallet_snapshots WHERE wallet = ? AND ts < ?").bind(wallet, timestamp() - 180 * 86400)
      ]);
      return Response.json({saved: true, observed_ts: now});
    }
    if (action === "history" && method === "GET") {
      if (!env.HELIUS_API_KEY) throw new ApiError(503, "HELIUS_API_KEY is not configured. Decoded historical swaps require Helius; RPC transfers are not treated as trades.");
      const {start, end} = coverage(url), before = url.searchParams.get("before"); if (before) signature(before);
      const params = new URLSearchParams({"api-key": env.HELIUS_API_KEY, "gte-time": String(start), "lte-time": String(end), "limit": "100", "sort-order": "desc", "token-accounts": "balanceChanged", "commitment": "finalized"});
      if (before) params.set("before-signature", before);
      const rows = await remember(`enhanced:${wallet}:${start}:${end}:${before || ""}`, 60, () => upstream(`https://mainnet.helius-rpc.com/v0/addresses/${wallet}/transactions?${params}`, {}, "Helius history"));
      if (!Array.isArray(rows)) throw new ApiError(502, "Helius returned an invalid history response.");
      const cursor = rows[rows.length - 1]?.signature || null;
      return Response.json({wallet, kind: "REAL", provider: "Helius Enhanced Transactions", retrieved_at: retrieved(), transactions: rows, next_cursor: cursor && cursor !== before ? cursor : null, coverage_complete: rows.length === 0, requested_start: start, requested_end: end});
    }
  }
  if (path.startsWith("/api/")) throw new ApiError(404, "API route not found.");
  if (env.ASSETS) return env.ASSETS.fetch(request);
  throw new ApiError(404, "Asset not found.");
}
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      const response = await routes(request, env);
      const headers = new Headers(response.headers);
      headers.set("X-Content-Type-Options", "nosniff"); headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
      if (new URL(request.url).pathname.startsWith("/api/")) headers.set("Cache-Control", "no-store");
      return new Response(response.body, {status: response.status, headers});
    } catch (e) {
      const error = e instanceof ApiError ? e : new ApiError(503, "The service or database is unavailable. Please retry shortly.");
      // Do not leak upstream URLs, credential headers, SQL or raw exceptions.
      return Response.json({detail: error.message}, {status: error.status, headers: {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}});
    }
  }
};
