import {address, ApiError, Env, finite, remember, retrieved, timestamp, upstream, WSOL} from "./runtime";
export type TokenMarket = {mint: string; symbol: string | null; name: string | null; price_usd: number | null; change_24h_pct: number | null; volume_24h_usd: number | null; liquidity_usd: number | null; market_cap_usd: number | null; fdv_usd: number | null; pair_address: string | null; dex: string | null; provider: string; retrieved_at: string; limitations: string[]};
function pairMarket(pair: any): TokenMarket {
  return {mint: address(pair.baseToken.address), symbol: pair.baseToken.symbol || null, name: pair.baseToken.name || null, price_usd: finite(pair.priceUsd), change_24h_pct: finite(pair.priceChange?.h24), volume_24h_usd: finite(pair.volume?.h24), liquidity_usd: finite(pair.liquidity?.usd), market_cap_usd: finite(pair.marketCap), fdv_usd: finite(pair.fdv), pair_address: pair.pairAddress || null, dex: pair.dexId || null, provider: "DEX Screener", retrieved_at: retrieved(), limitations: ["Price, volume and liquidity refer to the deepest returned base-token pair, not the entire token market.", "Pair creation time is not token creation time. Current liquidity must never be used in historical backtests."]};
}
export class MarketDataService {
  constructor(private env: Env) {}
  private cgHeaders(): Record<string,string> {return this.env.COINGECKO_DEMO_API_KEY ? {"x-cg-demo-api-key": this.env.COINGECKO_DEMO_API_KEY} : {};}
  async sol(): Promise<TokenMarket> {
    return remember("sol:" + (this.env.COINGECKO_DEMO_API_KEY || "public"), 60, async () => {
      try {
        const data = await upstream("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=solana", {headers: this.cgHeaders()}, "CoinGecko");
        if (!Array.isArray(data) || !data[0] || data[0].id !== "solana" || (finite(data[0].current_price) || 0) <= 0) throw new ApiError(502, "SOL market data is unavailable.");
        const d = data[0]; return {mint: WSOL, symbol: "SOL", name: "Solana", price_usd: finite(d.current_price), change_24h_pct: finite(d.price_change_percentage_24h), volume_24h_usd: finite(d.total_volume), market_cap_usd: finite(d.market_cap), fdv_usd: finite(d.fully_diluted_valuation), liquidity_usd: null, pair_address: null, dex: null, provider: "CoinGecko", retrieved_at: retrieved(), limitations: ["Aggregated current SOL market data. CoinGecko does not provide executable liquidity in this response."]};
      } catch (error) {
        if (!(error instanceof ApiError)) throw error;
        try {
          const quote = (await this.tokens([WSOL])).find(q => q.price_usd !== null && q.price_usd > 0);
          if (!quote) throw new ApiError(404, "No usable wSOL base-token pool quote was returned.");
          return {...quote, limitations: [...quote.limitations, `${error.message} Showing an actual wSOL pool quote instead of aggregated SOL market data.`]};
        } catch (fallback) {
          if (!(fallback instanceof ApiError)) throw fallback;
          throw new ApiError(error.status === 429 ? 429 : 503, `${error.message} The bounded DEX Screener alternative also failed: ${fallback.message}`);
        }
      }
    });
  }
  async tokens(mints: string[]): Promise<TokenMarket[]> {
    const valid = [...new Set(mints.map(address))]; if (valid.length > 60) throw new ApiError(422, "At most 60 tokens can be quoted per request.");
    const output: TokenMarket[] = [];
    for (let i = 0; i < valid.length; i += 30) {
      const chunk = valid.slice(i, i + 30).sort();
      const pairs = await remember("dex:" + chunk.join(","), 60, () => upstream("https://api.dexscreener.com/tokens/v1/solana/" + chunk.join(","), {}, "DEX Screener"));
      if (!Array.isArray(pairs)) throw new ApiError(502, "Token market data is unavailable.");
      for (const mint of chunk) {
        const sorted = pairs.filter(p => p.chainId === "solana" && p.baseToken?.address === mint).sort((a, b) => (finite(b.liquidity?.usd) || 0) - (finite(a.liquidity?.usd) || 0));
        if (sorted[0]) output.push(pairMarket(sorted[0]));
      }
    }
    return output;
  }
  async token(mint: string): Promise<TokenMarket> {
    address(mint); if (mint === WSOL) return this.sol();
    const rows = await this.tokens([mint]); if (!rows.length) throw new ApiError(404, "No supported Solana market was found for this mint. Its price and metadata are unavailable."); return rows[0];
  }
  async search(query: string): Promise<TokenMarket[]> {
    if (!query.trim() || query.length > 80) throw new ApiError(422, "Enter a token symbol, name or mint (1–80 characters).");
    return remember("search:" + query.trim().toLowerCase(), 60, async () => {
      const data = await upstream("https://api.dexscreener.com/latest/dex/search?q=" + encodeURIComponent(query.trim()), {}, "DEX Screener");
      const unique = new Map<string, TokenMarket>();
      for (const pair of (data.pairs || []).filter((p: any) => p.chainId === "solana" && p.baseToken?.address).sort((a: any, b: any) => (finite(b.liquidity?.usd) || 0) - (finite(a.liquidity?.usd) || 0))) {
        try {const token = pairMarket(pair); if (!unique.has(token.mint)) unique.set(token.mint, token);} catch {/* Invalid provider address is not shown. */}
      }
      return [...unique.values()].slice(0, 20);
    });
  }
  async history(mint: string, days: number) {
    address(mint); if (![1, 7, 30].includes(days)) throw new ApiError(422, "Select 1, 7 or 30 days of price history.");
    return remember(`history:${mint}:${days}:${Boolean(this.env.BIRDEYE_API_KEY)}`, 300, async () => {
      let points: {ts: number; price_usd: number}[] = [], provider: string, resolution = 3600, limitations: string[];
      if (mint === WSOL && !this.env.BIRDEYE_API_KEY) {
        const d = await upstream(`https://api.coingecko.com/api/v3/coins/solana/market_chart?vs_currency=usd&days=${days}`, {headers: this.cgHeaders()}, "CoinGecko history");
        points = (d.prices || []).filter((p: any) => Array.isArray(p) && finite(p[0]) !== null && (finite(p[1]) || 0) > 0).map((p: any) => ({ts: Math.floor(p[0] / 1000), price_usd: Number(p[1])}));
        resolution = days === 1 ? 300 : 3600; provider = "CoinGecko"; limitations = ["Provider-sampled USD history. Actual timestamps are retained; no interpolation is performed.", "Price history alone is not an executable research dataset; historical liquidity is unavailable here."];
      } else if (this.env.BIRDEYE_API_KEY) {
        const now = timestamp();
        const d = await upstream(`https://public-api.birdeye.so/defi/history_price?address=${mint}&address_type=token&type=1H&time_from=${now - days * 86400}&time_to=${now}&ui_amount_mode=raw`, {headers: {"X-API-KEY": this.env.BIRDEYE_API_KEY, "x-chain": "solana"}}, "Birdeye history");
        if (!d.success || d.data?.isScaledUiToken) throw new ApiError(503, "This token's historical prices cannot be normalized safely.");
        points = (d.data?.items || []).filter((p: any) => (finite(p.value) || 0) > 0 && Number.isInteger(p.unixTime)).map((p: any) => ({ts: p.unixTime + 3600, price_usd: Number(p.value)})).filter((p: any) => p.ts <= now);
        provider = "Birdeye"; limitations = ["Hourly provider marks, available after the bucket closes. Missing points are not filled.", "This chart has no historical liquidity; research ingestion retrieves it separately."];
      } else {
        const pools = await upstream(`https://api.geckoterminal.com/api/v2/networks/solana/tokens/${mint}/pools?page=1`, {headers: {Accept: "application/json"}}, "GeckoTerminal");
        const basePools = (pools.data || []).filter((p: any) => p.relationships?.base_token?.data?.id === "solana_" + mint).sort((a: any, b: any) => (finite(b.attributes?.reserve_in_usd) || 0) - (finite(a.attributes?.reserve_in_usd) || 0));
        const pool = basePools[0]?.attributes?.address;
        if (!pool) throw new ApiError(404, "No supported base-token pool history was found. No price chart has been fabricated.");
        address(pool);
        const now = timestamp(), count = Math.min(days * 24, 720);
        const data = await upstream(`https://api.geckoterminal.com/api/v2/networks/solana/pools/${pool}/ohlcv/hour?aggregate=1&limit=${count}&currency=usd&token=base&include_empty_intervals=false`, {}, "GeckoTerminal OHLCV");
        points = (data.data?.attributes?.ohlcv_list || []).filter((p: any) => Array.isArray(p) && (finite(p[4]) || 0) > 0 && Number.isInteger(p[0]) && p[0] + 3600 <= now).map((p: any) => ({ts: p[0] + 3600, price_usd: Number(p[4])}));
        provider = "GeckoTerminal"; limitations = [`Closed hourly candles from pool ${pool}. This is one pool, not a consolidated market.`, "Empty intervals are omitted. No historical liquidity is inferred from current pool reserves."];
      }
      points = [...new Map(points.map(p => [p.ts, p])).values()].sort((a, b) => a.ts - b.ts);
      if (!points.length) throw new ApiError(404, "No historical price observations were returned for this token.");
      return {mint, kind: "REAL", points, provider, resolution_seconds: resolution, retrieved_at: retrieved(), limitations};
    });
  }
}
