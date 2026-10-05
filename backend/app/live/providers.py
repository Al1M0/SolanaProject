"""Read-only Solana and market service layer. No private keys or transaction sending."""
from collections import OrderedDict
from datetime import datetime, timezone
import math
import threading
import time
import httpx

WSOL = "So11111111111111111111111111111111111111112"
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAINNET_GENESIS = "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d"
TOKEN_PROGRAMS = ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")

class LiveError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)

def decode58(text):
    if not isinstance(text, str) or not 1 <= len(text) <= 90:
        raise LiveError(422, "Invalid Solana address or signature.")
    value = 0
    for char in text:
        if char not in BASE58:
            raise LiveError(422, "Invalid base58 Solana address.")
        value = value * 58 + BASE58.index(char)
    encoded = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return b"\0" * (len(text) - len(text.lstrip("1"))) + encoded

def address(text):
    if len(decode58(text)) != 32:
        raise LiveError(422, "Enter a valid 32-byte Solana public address.")
    return text

def signature(text):
    if len(decode58(text)) != 64:
        raise LiveError(422, "Invalid Solana transaction signature.")
    return text

def finite(value):
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None

def retrieved():
    return datetime.now(timezone.utc).isoformat()

class Cache:
    """Bounded TTL cache plus same-key request deduplication, safe across API threads."""
    def __init__(self):
        self.data, self.locks, self.guard = OrderedDict(), {}, threading.Lock()

    def get(self, key, seconds, work):
        with self.guard:
            flight = self.locks.setdefault(key, [threading.Lock(), 0])
            flight[1] += 1
        try:
            with flight[0]:
                with self.guard:
                    cached = self.data.get(key)
                    if cached and cached[0] > time.monotonic():
                        return cached[1]
                value = work()
                with self.guard:
                    self.data[key] = (time.monotonic() + seconds, value)
                    while len(self.data) > 256:
                        self.data.popitem(last=False)
                return value
        finally:
            with self.guard:
                flight[1] -= 1
                if flight[1] == 0:
                    self.locks.pop(key, None)

CACHE = Cache()

class HttpProvider:
    def __init__(self, client=None):
        self.client = client or httpx.Client(timeout=10)

    def request(self, method, url, label, **kwargs):
        for attempt in range(2):
            try:
                response = self.client.request(method, url, **kwargs)
            except httpx.TransportError:
                if attempt == 0:
                    continue
                raise LiveError(503, f"{label} did not respond. Retry shortly; no demo data was substituted.") from None
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 0:
                    time.sleep(.1)
                    continue
                raise LiveError(429 if response.status_code == 429 else 503, f"{label} rate limit reached or temporarily unavailable. Retry shortly.")
            if response.status_code >= 400:
                raise LiveError(503, f"{label} rejected the request (HTTP {response.status_code}). Check provider access or API plan.")
            try:
                return response.json()
            except ValueError:
                raise LiveError(502, f"{label} returned an invalid response.") from None

class MarketDataService(HttpProvider):
    def __init__(self, settings, client=None):
        super().__init__(client)
        self.settings = settings
        self.cg_headers = {"x-cg-demo-api-key": settings.coingecko_demo_api_key} if settings.coingecko_demo_api_key else {}

    def sol(self):
        def work():
            try:
                rows = self.request("GET", "https://api.coingecko.com/api/v3/coins/markets", "CoinGecko", params={"vs_currency": "usd", "ids": "solana"}, headers=self.cg_headers)
                if not isinstance(rows, list) or not rows or rows[0].get("id") != "solana" or (finite(rows[0].get("current_price")) or 0) <= 0:
                    raise LiveError(502, "SOL market data is unavailable.")
                d = rows[0]
                return {"mint": WSOL, "symbol": "SOL", "name": "Solana", "price_usd": finite(d.get("current_price")), "change_24h_pct": finite(d.get("price_change_percentage_24h")), "volume_24h_usd": finite(d.get("total_volume")), "market_cap_usd": finite(d.get("market_cap")), "fdv_usd": finite(d.get("fully_diluted_valuation")), "liquidity_usd": None, "pair_address": None, "dex": None, "provider": "CoinGecko", "retrieved_at": retrieved(), "limitations": ["Aggregated current SOL market data. This response does not provide executable liquidity."]}
            except LiveError as error:
                try:
                    quote = next((q for q in self.tokens([WSOL]) if q["price_usd"] is not None and q["price_usd"] > 0), None)
                    if not quote:
                        raise LiveError(404, "No usable wSOL base-token pool quote was returned.")
                    return {**quote, "limitations": [*quote["limitations"], f"{error} Showing an actual wSOL pool quote instead of aggregated SOL market data."]}
                except LiveError as fallback:
                    raise LiveError(429 if error.status == 429 else 503, f"{error} The bounded DEX Screener alternative also failed: {fallback}") from None
        return CACHE.get(("sol", self.settings.coingecko_demo_api_key, self.client), 60, work)

    @staticmethod
    def pair(pair):
        return {"mint": address(pair["baseToken"]["address"]), "symbol": pair["baseToken"].get("symbol"), "name": pair["baseToken"].get("name"), "price_usd": finite(pair.get("priceUsd")), "change_24h_pct": finite((pair.get("priceChange") or {}).get("h24")), "volume_24h_usd": finite((pair.get("volume") or {}).get("h24")), "liquidity_usd": finite((pair.get("liquidity") or {}).get("usd")), "market_cap_usd": finite(pair.get("marketCap")), "fdv_usd": finite(pair.get("fdv")), "pair_address": pair.get("pairAddress"), "dex": pair.get("dexId"), "provider": "DEX Screener", "retrieved_at": retrieved(), "limitations": ["Prices, volume and liquidity refer to one deepest returned base-token pair, not the entire token market.", "Current liquidity is never substituted for historical liquidity. Pair creation time is not token creation time."]}

    def tokens(self, mints):
        mints = sorted(set(address(m) for m in mints))
        if len(mints) > 60:
            raise LiveError(422, "At most 60 tokens can be quoted per request.")
        rows = []
        for left in range(0, len(mints), 30):
            chunk = mints[left:left + 30]
            pairs = CACHE.get(("dex", tuple(chunk), self.client), 60, lambda: self.request("GET", "https://api.dexscreener.com/tokens/v1/solana/" + ",".join(chunk), "DEX Screener"))
            if not isinstance(pairs, list):
                raise LiveError(502, "Token market data is unavailable.")
            for mint in chunk:
                found = sorted((p for p in pairs if p.get("chainId") == "solana" and (p.get("baseToken") or {}).get("address") == mint), key=lambda p: finite((p.get("liquidity") or {}).get("usd")) or 0, reverse=True)
                if found:
                    rows.append(self.pair(found[0]))
        return rows

    def token(self, mint):
        address(mint)
        if mint == WSOL:
            return self.sol()
        rows = self.tokens([mint])
        if not rows:
            raise LiveError(404, "No supported Solana market was found for this mint.")
        return rows[0]

    def search(self, query):
        if not query.strip() or len(query) > 80:
            raise LiveError(422, "Enter a token symbol, name or mint (1–80 characters).")
        data = CACHE.get(("search", query.lower(), self.client), 60, lambda: self.request("GET", "https://api.dexscreener.com/latest/dex/search", "DEX Screener", params={"q": query.strip()}))
        found = {}
        for pair in sorted((p for p in data.get("pairs", []) if p.get("chainId") == "solana" and (p.get("baseToken") or {}).get("address")), key=lambda p: finite((p.get("liquidity") or {}).get("usd")) or 0, reverse=True):
            try:
                value = self.pair(pair)
                found.setdefault(value["mint"], value)
            except LiveError:
                pass
        return list(found.values())[:20]

    def history(self, mint, days):
        address(mint)
        if days not in (1, 7, 30):
            raise LiveError(422, "Select 1, 7 or 30 days of history.")
        def work():
            resolution, now = 3600, int(time.time())
            if mint == WSOL and not self.settings.birdeye_api_key:
                d = self.request("GET", "https://api.coingecko.com/api/v3/coins/solana/market_chart", "CoinGecko history", params={"vs_currency": "usd", "days": days}, headers=self.cg_headers)
                points = [{"ts": int(p[0] // 1000), "price_usd": float(p[1])} for p in d.get("prices", []) if isinstance(p, list) and len(p) >= 2 and (finite(p[1]) or 0) > 0]
                resolution, provider = (300 if days == 1 else 3600), "CoinGecko"
            elif self.settings.birdeye_api_key:
                d = self.request("GET", "https://public-api.birdeye.so/defi/history_price", "Birdeye history", params={"address": mint, "address_type": "token", "type": "1H", "time_from": now - days * 86400, "time_to": now, "ui_amount_mode": "raw"}, headers={"X-API-KEY": self.settings.birdeye_api_key, "x-chain": "solana"})
                if not d.get("success") or d.get("data", {}).get("isScaledUiToken"):
                    raise LiveError(503, "Historical token prices cannot be normalized safely.")
                points = [{"ts": p["unixTime"] + 3600, "price_usd": float(p["value"])} for p in d.get("data", {}).get("items", []) if isinstance(p.get("unixTime"), int) and (finite(p.get("value")) or 0) > 0 and p["unixTime"] + 3600 <= now]
                provider = "Birdeye"
            else:
                pools = self.request("GET", f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}/pools", "GeckoTerminal", params={"page": 1})
                eligible = [p for p in pools.get("data", []) if p.get("relationships", {}).get("base_token", {}).get("data", {}).get("id") == "solana_" + mint]
                eligible.sort(key=lambda p: finite(p.get("attributes", {}).get("reserve_in_usd")) or 0, reverse=True)
                if not eligible:
                    raise LiveError(404, "No supported base-token pool history was found.")
                pool = address(eligible[0]["attributes"]["address"])
                d = self.request("GET", f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}/ohlcv/hour", "GeckoTerminal OHLCV", params={"aggregate": 1, "limit": min(days * 24, 720), "currency": "usd", "token": "base", "include_empty_intervals": "false"})
                points = [{"ts": p[0] + 3600, "price_usd": float(p[4])} for p in d.get("data", {}).get("attributes", {}).get("ohlcv_list", []) if len(p) >= 5 and isinstance(p[0], int) and (finite(p[4]) or 0) > 0 and p[0] + 3600 <= now]
                provider = "GeckoTerminal"
            points = sorted({p["ts"]: p for p in points}.values(), key=lambda p: p["ts"])
            if not points:
                raise LiveError(404, "No historical price observations were returned.")
            return {"mint": mint, "kind": "REAL", "points": points, "provider": provider, "resolution_seconds": resolution, "retrieved_at": retrieved(), "limitations": ["Actual provider timestamps, no interpolation or synthetic gap filling. Pool candles become available after bucket close.", "This display series has no historical liquidity; historical research requires separate complete observations."]}
        return CACHE.get(("history", mint, days, self.client), 300, work)

class SolanaService(HttpProvider):
    def __init__(self, settings, client=None):
        super().__init__(client)
        self.url = settings.solana_rpc_url or (f"https://mainnet.helius-rpc.com/?api-key={settings.helius_api_key}" if settings.helius_api_key else "https://api.mainnet-beta.solana.com")

    def batch(self, calls):
        if len(calls) > 25:
            raise LiveError(422, "RPC batch is too large.")
        rows = self.request("POST", self.url, "Solana mainnet RPC", json=[{"jsonrpc": "2.0", "id": i, **call} for i, call in enumerate(calls)])
        if not isinstance(rows, list):
            raise LiveError(502, "RPC did not accept the read-only batch.")
        result = []
        for i in range(len(calls)):
            row = next((r for r in rows if r.get("id") == i), None)
            if not row or row.get("error"):
                raise LiveError(429 if row and row.get("error", {}).get("code") == 429 else 503, "Solana RPC could not complete the read. Check provider access and rate limits.")
            result.append(row.get("result"))
        return result

    def mainnet(self):
        def verify():
            if self.batch([{"method": "getGenesisHash"}])[0] != MAINNET_GENESIS:
                raise LiveError(503, "RPC must point to Solana mainnet-beta. Testnet data is not substituted.")
            return True
        return CACHE.get(("genesis", self.url, self.client), 3600, verify)

    def balances(self, wallet):
        address(wallet)
        self.mainnet()
        def work():
            balance, spl, token22 = self.batch([{"method": "getBalance", "params": [wallet, {"commitment": "confirmed"}]}] + [{"method": "getTokenAccountsByOwner", "params": [wallet, {"programId": program}, {"encoding": "jsonParsed", "commitment": "confirmed"}]} for program in TOKEN_PROGRAMS])
            if not isinstance((balance or {}).get("value"), int) or balance["value"] < 0 or not isinstance((spl or {}).get("value"), list) or not isinstance((token22 or {}).get("value"), list):
                raise LiveError(502, "RPC returned incomplete wallet balances.")
            tokens = {}
            for row in spl["value"] + token22["value"]:
                info = row.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                amount = info.get("tokenAmount", {})
                raw, decimals = str(amount.get("amount", "")), amount.get("decimals")
                if not raw.isdigit() or not isinstance(decimals, int) or not 0 <= decimals <= 255 or int(raw) == 0 or not info.get("mint"):
                    continue
                mint = address(info["mint"])
                prior = tokens.get(mint)
                if prior and prior["decimals"] != decimals:
                    raise LiveError(502, "Conflicting token decimals.")
                total = int(raw) + int(prior["raw_amount"] if prior else 0)
                encoded = str(total).zfill(decimals + 1)
                ui = encoded[:-decimals] + "." + encoded[-decimals:] if decimals else encoded
                supported = not any(e.get("extension") in ("scaledUiAmountConfig", "interestBearingConfig") for e in info.get("extensions", [])) and (not prior or prior["valuation_supported"])
                tokens[mint] = {"mint": mint, "decimals": decimals, "raw_amount": str(total), "amount": ui, "token_program": row["account"].get("owner"), "valuation_supported": supported}
            return {"wallet": wallet, "sol_balance": balance["value"] / 1e9, "balance_lamports": balance["value"], "slot": balance.get("context", {}).get("slot"), "tokens": list(tokens.values()), "network": "mainnet-beta", "kind": "REAL", "provider": "Solana JSON-RPC", "retrieved_at": retrieved()}
        return CACHE.get(("balances", wallet, self.url, self.client), 30, work)

    def transactions(self, wallet, before=None):
        address(wallet)
        if before:
            signature(before)
        self.mainnet()
        def work():
            rows = self.batch([{"method": "getSignaturesForAddress", "params": [wallet, {"limit": 20, "commitment": "confirmed", **({"before": before} if before else {})}]}])[0]
            if not isinstance(rows, list):
                raise LiveError(502, "RPC returned invalid transaction history.")
            rows = list({r["signature"]: r for r in rows}.values())
            details, warning = [], None
            if rows:
                try:
                    details = self.batch([{"method": "getTransaction", "params": [r["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}]} for r in rows[:10]])
                except LiveError as exc:
                    warning = str(exc)
            result = []
            for i, r in enumerate(rows):
                detail = (details[i] if i < len(details) else None) or {}
                names = [x["parsed"].get("type") for x in detail.get("transaction", {}).get("message", {}).get("instructions", []) if x.get("parsed")]
                kind = "FAILED" if r.get("err") else "TRANSFER" if names and all(n in ("transfer", "transferChecked") for n in names) else None
                fee = finite((detail.get("meta") or {}).get("fee"))
                result.append({"signature": r["signature"], "ts": r.get("blockTime"), "slot": r.get("slot"), "status": "failed" if r.get("err") else "confirmed", "type": kind, "fee_lamports": fee, "fee_sol": fee / 1e9 if fee is not None else None, "explorer_url": f"https://explorer.solana.com/tx/{r['signature']}?cluster=mainnet-beta", "solscan_url": f"https://solscan.io/tx/{r['signature']}"})
            return {"wallet": wallet, "kind": "REAL", "transactions": result, "next_cursor": rows[-1]["signature"] if len(rows) == 20 else None, "warning": warning, "provider": "Solana JSON-RPC", "retrieved_at": retrieved(), "limitations": ["Twenty signatures per page; at most ten detailed records. Unknown types and fees remain N/A.", "Transfers are not classified as swaps. RPC history can be pruned."]}
        return CACHE.get(("transactions", wallet, before, self.url, self.client), 30, work)

class WalletService:
    def __init__(self, solana, market):
        self.solana, self.market = solana, market

    def snapshot(self, wallet):
        data, warnings = self.solana.balances(wallet), []
        sol_price, quotes = None, []
        try:
            sol_price = self.market.sol()["price_usd"]
        except LiveError as exc:
            warnings.append(str(exc))
        mints = [t["mint"] for t in data["tokens"] if t["valuation_supported"]][:60]
        if mints:
            try:
                quotes = self.market.tokens(mints)
            except LiveError as exc:
                warnings.append(str(exc))
        tokens = []
        for t in data["tokens"]:
            quote = next((q for q in quotes if q["mint"] == t["mint"]), {})
            price = sol_price if t["mint"] == WSOL else quote.get("price_usd")
            price = price if t["valuation_supported"] else None
            tokens.append({**t, "symbol": quote.get("symbol", "wSOL" if t["mint"] == WSOL else None), "name": quote.get("name"), "price_usd": price, "value_usd": finite(float(t["amount"]) * price) if price is not None else None})
        sol_value = data["sol_balance"] * sol_price if sol_price is not None else None
        unpriced = sum(t["value_usd"] is None for t in tokens)
        known = sol_value is not None or any(t["value_usd"] is not None for t in tokens)
        return {**data, "tokens": tokens, "sol_price_usd": sol_price, "sol_value_usd": sol_value, "valued_subtotal_usd": (sol_value or 0) + sum(t["value_usd"] or 0 for t in tokens) if known else None, "portfolio_complete": unpriced == 0 and sol_value is not None, "unpriced_tokens": unpriced, "warnings": warnings, "limitations": ["USD values are current-price estimates, not executable proceeds. Unknown prices are omitted from the valued subtotal.", "Up to 60 positive holdings are quoted. Scaled-UI and interest-bearing extensions require explicit normalization and are not valued."]}
