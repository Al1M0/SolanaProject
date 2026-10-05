import {Env, retrieved, upstream, WSOL} from "./runtime";

export async function providerReadiness(env: Env) {
  const now = Math.floor(Date.now() / 300000) * 300 - 600;
  const probes = [
    {endpoint: "Helius decoded wallet history", key: env.HELIUS_API_KEY, url: `https://mainnet.helius-rpc.com/v0/addresses/${WSOL}/transactions?api-key=${env.HELIUS_API_KEY}&limit=1&gte-time=${now-300}&lte-time=${now}`, headers: undefined},
    {endpoint: "Birdeye historical 5m price", key: env.BIRDEYE_API_KEY, url: `https://public-api.birdeye.so/defi/history_price?address=${WSOL}&address_type=token&type=5m&time_from=${now-300}&time_to=${now}&ui_amount_mode=raw`, headers: {"X-API-KEY": env.BIRDEYE_API_KEY || "", "x-chain": "solana"}},
    {endpoint: "Birdeye historical exit liquidity", key: env.BIRDEYE_API_KEY, url: `https://public-api.birdeye.so/defi/v3/liquidity/history/token?address=${WSOL}&resolution=1m&time=${now}&direction=back&count=1`, headers: {"X-API-KEY": env.BIRDEYE_API_KEY || "", "x-chain": "solana"}}
  ];
  const checks = [];
  for (const p of probes) {
    if (!p.key) {checks.push({endpoint: p.endpoint, status: "missing_key", message: p.endpoint.startsWith("Helius") ? "HELIUS_API_KEY missing" : "BIRDEYE_API_KEY missing"}); continue;}
    try {
      const r = await upstream(p.url, {headers: p.headers}, p.endpoint);
      const ok = p.endpoint.startsWith("Helius") ? Array.isArray(r) : r.success === true && Array.isArray(r.data?.items);
      checks.push({endpoint: p.endpoint, status: ok ? "accessible" : "unverified", message: ok ? "Endpoint responded; study coverage still requires verification" : "Plan or response shape could not be verified"});
    } catch (e) {checks.push({endpoint: p.endpoint, status: "blocked", message: e instanceof Error ? e.message : "Access blocked"});}
  }
  return {ready: checks.every(c => c.status === "accessible"), checks, checked_at: retrieved(), max_provider_attempts: 6, scope: "Endpoint access only; account quota, complete historical coverage and redistribution rights remain unverified"};
}
