import {address, ApiError, Env, finite, remember, retrieved, signature, upstream, WSOL} from "./runtime";
import {MarketDataService} from "./market";
const TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb";
type Call = {method: string; params?: unknown[]};
export class SolanaService {
  private url: string;
  constructor(env: Env) {this.url = env.SOLANA_RPC_URL || (env.HELIUS_API_KEY ? "https://mainnet.helius-rpc.com/?api-key=" + encodeURIComponent(env.HELIUS_API_KEY) : "https://api.mainnet-beta.solana.com");}
  async batch(calls: Call[]): Promise<any[]> {
    if (calls.length > 25) throw new ApiError(422, "RPC batch is too large.");
    const response = await upstream(this.url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(calls.map((c, i) => ({jsonrpc: "2.0", id: i, ...c})))}, "Solana mainnet RPC");
    if (!Array.isArray(response)) throw new ApiError(502, "Solana RPC did not accept the read-only batch.");
    return calls.map((_, i) => {const r = response.find(x => x.id === i); if (!r || r.error) throw new ApiError(r?.error?.code === 429 ? 429 : 503, "Solana RPC could not complete the read. Check RPC access and rate limits."); return r.result;});
  }
  async verifyNetwork() {return remember("genesis:" + this.url, 3600, async () => {const [hash] = await this.batch([{method: "getGenesisHash"}]); if (hash !== "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d") throw new ApiError(503, "RPC must point to Solana mainnet-beta. Testnet data is not substituted."); return true;});}
  async balances(wallet: string) {
    address(wallet); await this.verifyNetwork();
    return remember("balances:" + this.url + wallet, 30, async () => {
      const [balance, spl, token22] = await this.batch([
        {method: "getBalance", params: [wallet, {commitment: "confirmed"}]},
        ...[TOKEN_PROGRAM, TOKEN_2022].map(programId => ({method: "getTokenAccountsByOwner", params: [wallet, {programId}, {encoding: "jsonParsed", commitment: "confirmed"}]}))
      ]);
      if (!Number.isSafeInteger(balance?.value) || balance.value < 0 || !Array.isArray(spl?.value) || !Array.isArray(token22?.value)) throw new ApiError(502, "Solana RPC returned incomplete wallet balances.");
      const holdings = new Map<string, any>();
      for (const record of [...spl.value, ...token22.value]) {
        const info = record.account?.data?.parsed?.info, amount = info?.tokenAmount;
        if (!info?.mint || !amount || !/^\d+$/.test(String(amount.amount)) || !Number.isInteger(amount.decimals) || amount.decimals < 0 || amount.decimals > 255 || BigInt(amount.amount) === 0n) continue;
        const extensions = info.extensions || [], supported = !extensions.some((e: any) => ["scaledUiAmountConfig", "interestBearingConfig"].includes(e.extension));
        const prior = holdings.get(info.mint), raw = BigInt(amount.amount) + BigInt(prior?.raw_amount || 0);
        if (prior && prior.decimals !== amount.decimals) throw new ApiError(502, "Conflicting token decimals were returned.");
        const padded = raw.toString().padStart(amount.decimals + 1, "0");
        const ui = amount.decimals ? padded.slice(0, -amount.decimals) + "." + padded.slice(-amount.decimals) : padded;
        holdings.set(address(info.mint), {mint: info.mint, decimals: amount.decimals, raw_amount: raw.toString(), amount: ui, token_program: record.account.owner, valuation_supported: supported && prior?.valuation_supported !== false});
      }
      return {wallet, sol_balance: balance.value / 1e9, balance_lamports: balance.value, slot: balance.context?.slot || null, tokens: [...holdings.values()], network: "mainnet-beta", kind: "REAL", provider: "Solana JSON-RPC", retrieved_at: retrieved()};
    });
  }
  async transactions(wallet: string, before?: string) {
    address(wallet); if (before) signature(before); await this.verifyNetwork();
    return remember("tx:" + this.url + wallet + (before || ""), 30, async () => {
      const [raw] = await this.batch([{method: "getSignaturesForAddress", params: [wallet, {limit: 20, commitment: "confirmed", ...(before ? {before} : {})}]}]);
      if (!Array.isArray(raw)) throw new ApiError(502, "Solana RPC returned invalid transaction history.");
      const rows = [...new Map(raw.map(x => [x.signature, x])).values()];
      // One bounded RPC batch. Fees/types stay null where detailed history is unavailable.
      let details: any[] = [], warning: string | null = null;
      if (rows.length) {try {details = await this.batch(rows.slice(0, 10).map(x => ({method: "getTransaction", params: [x.signature, {encoding: "jsonParsed", maxSupportedTransactionVersion: 0, commitment: "confirmed"}]})));} catch (e) {warning = e instanceof Error ? e.message : "Transaction details are unavailable.";}}
      const transactions = rows.map((s, i) => {
        const d = details[i], instructions = d?.transaction?.message?.instructions || [], names = instructions.filter((x: any) => x.parsed).map((x: any) => x.parsed.type);
        const type = s.err ? "FAILED" : names.length && names.every((n: string) => ["transfer", "transferChecked"].includes(n)) ? "TRANSFER" : null;
        return {signature: s.signature, ts: Number.isInteger(s.blockTime) ? s.blockTime : null, slot: s.slot, status: s.err ? "failed" : "confirmed", type, fee_lamports: finite(d?.meta?.fee), fee_sol: finite(d?.meta?.fee) === null ? null : d.meta.fee / 1e9, explorer_url: `https://explorer.solana.com/tx/${s.signature}?cluster=mainnet-beta`, solscan_url: `https://solscan.io/tx/${s.signature}`};
      });
      return {wallet, kind: "REAL", transactions, next_cursor: rows.length === 20 ? rows[rows.length - 1].signature : null, warning, provider: "Solana JSON-RPC", retrieved_at: retrieved(), limitations: ["Twenty signatures per page. Up to ten detailed transactions fetched per page; other fees and types remain N/A.", "RPC history may be pruned. Token transfers and unknown instructions are not treated as swaps."]};
    });
  }
}
export class WalletService {
  constructor(private env: Env) {}
  async snapshot(wallet: string) {
    const balances = await new SolanaService(this.env).balances(wallet), market = new MarketDataService(this.env), warnings: string[] = [];
    let solPrice: number | null = null, quotes: any[] = [];
    try {solPrice = (await market.sol()).price_usd;} catch (e) {warnings.push(e instanceof Error ? e.message : "SOL price is unavailable.");}
    const mints = balances.tokens.filter(t => t.valuation_supported).slice(0, 60).map(t => t.mint);
    if (mints.length) {try {quotes = await market.tokens(mints);} catch (e) {warnings.push(e instanceof Error ? e.message : "Token quotes are unavailable.");}}
    const tokens = balances.tokens.map(t => {const q = quotes.find(x => x.mint === t.mint); const price = t.mint === WSOL ? solPrice : q?.price_usd ?? null; return {...t, symbol: q?.symbol ?? (t.mint === WSOL ? "wSOL" : null), name: q?.name ?? null, price_usd: t.valuation_supported ? price : null, value_usd: t.valuation_supported && price !== null ? finite(Number(t.amount) * price) : null};});
    const solValue = solPrice !== null ? balances.sol_balance * solPrice : null, unpriced = tokens.filter(t => t.value_usd === null).length;
    const known = solValue !== null || tokens.some(t => t.value_usd !== null);
    return {...balances, tokens, sol_price_usd: solPrice, sol_value_usd: solValue, valued_subtotal_usd: known ? (solValue || 0) + tokens.reduce((s, t) => s + (t.value_usd || 0), 0) : null, portfolio_complete: unpriced === 0 && solValue !== null, unpriced_tokens: unpriced, warnings, limitations: ["USD values are estimates at current provider quotes, not executable proceeds.", "Only up to 60 positive token holdings are quoted. Missing prices are excluded from the valued subtotal.", "Scaled-UI and interest-bearing Token-2022 amounts are displayed but not valued without an explicit normalization model."]};
  }
}
