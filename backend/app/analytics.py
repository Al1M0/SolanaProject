"""Observed FIFO returns in actual quote units; missing USD is never a dollar PnL."""
from collections import Counter, defaultdict, deque
import math
import statistics
from .normalization import normalize_swap, WSOL, USDC, USDT

QUOTES = {WSOL: "SOL", USDC: "USDC", USDT: "USDT"}

def normalized_histories(histories):
    events, rejection, coverage, identities = {}, Counter(), [], set()
    for history in histories:
        wallet = history["wallet"]
        local = set()
        for tx in history.get("transactions", []):
            signature = tx.get("signature")
            if not signature or signature in local:
                rejection["duplicate_or_missing_signature"] += 1
                continue
            local.add(signature)
            if not isinstance(tx.get("timestamp"), int) or not history["requested_start"] <= tx["timestamp"] <= history["requested_end"]:
                rejection["outside_requested_coverage"] += 1
                continue
            rows, reason = normalize_swap(tx, wallet)
            for event in rows:
                events[event["id"]] = event
            if reason:
                rejection[reason] += 1
        coverage.append({k: history.get(k) for k in ("wallet", "coverage_complete", "requested_start", "requested_end", "retrieved_at", "provider")})
        identities.update((wallet, s) for s in local)
    return sorted(events.values(), key=lambda e: (e["ts"], e.get("slot", 0), e["id"])), {"wallet_ingestion": coverage, "rejected": dict(rejection), "observed_transactions": len(identities), "transaction_coverage_complete": all(h.get("coverage_complete") is True for h in histories)}

class QuoteLedger:
    def __init__(self):
        self.lots, self.closed = defaultdict(deque), defaultdict(list)
        self.unmatched_sales = Counter()

    def observe(self, e):
        q, amount = e["quantity"], e["quote_quantity"]
        price = amount / q
        key = (e["wallet"], e["token"], e["quote_mint"])
        if e["side"] == "buy":
            self.lots[key].append([q, price])
            return
        cost = proceeds = matched_total = 0.0
        while q > 1e-10 and self.lots[key]:
            lot = self.lots[key][0]
            matched = min(q, lot[0])
            cost += matched * lot[1]
            proceeds += matched * price
            matched_total += matched
            lot[0] -= matched
            q -= matched
            if lot[0] < 1e-10:
                self.lots[key].popleft()
        if q > 1e-10:
            self.unmatched_sales[e["wallet"]] += 1
        if cost > 0:
            self.closed[e["wallet"]].append({"ts": e["ts"], "token": e["token"], "quote_mint": e["quote_mint"], "cost": cost, "proceeds": proceeds, "matched_quantity": matched_total, "partial": q > 1e-10, "return_pct": (proceeds / cost - 1) * 100})

    def score(self, wallet, before):
        rows = [r for r in self.closed[wallet] if r["ts"] < before and not r["partial"]]
        return {"closed_sales": len(rows), "average_return_pct": statistics.mean(r["return_pct"] for r in rows) if rows else None}

def wallet_analytics(histories, minimum_sample=10):
    events, metadata = normalized_histories(histories)
    ledger = QuoteLedger()
    for event in events:
        ledger.observe(event)
    wallets = []
    for history in histories:
        wallet = history["wallet"]
        observed = [e for e in events if e["wallet"] == wallet]
        closed = ledger.closed[wallet]
        complete_sales = [r for r in closed if not r["partial"]]
        returns = [r["return_pct"] for r in complete_sales]
        quote_pnl = {QUOTES.get(q, q): sum(r["proceeds"] - r["cost"] for r in closed if r["quote_mint"] == q) for q in {r["quote_mint"] for r in closed}}
        days = (history["requested_end"] - history["requested_start"]) / 86400
        sufficient = len(complete_sales) >= minimum_sample and history.get("coverage_complete") is True
        wallets.append({"wallet": wallet, "observed_trades": len(observed), "buys": sum(e["side"] == "buy" for e in observed), "sells": sum(e["side"] == "sell" for e in observed), "closed_sales": len(complete_sales), "partial_matched_sales": len(closed) - len(complete_sales), "unmatched_sales": ledger.unmatched_sales[wallet], "win_rate_pct": sum(r > 0 for r in returns) / len(returns) * 100 if returns else None, "average_return_pct": statistics.mean(returns) if returns else None, "median_return_pct": statistics.median(returns) if returns else None, "observed_matched_pnl_by_quote": quote_pnl, "realized_pnl_usd": None, "trades_per_observed_day": len(observed) / days if days > 0 else None, "tokens_traded": len({e["token"] for e in observed}), "coverage_complete": history.get("coverage_complete") is True, "minimum_sample": minimum_sample, "evidence_status": "Observed sample available" if sufficient else "Insufficient historical data", "recent_activity": observed[-20:][::-1]})
    return {"kind": "REAL", "wallets": wallets, "events": events, "provenance": metadata, "limitations": ["Only explicit, unambiguous wallet-owned swap endpoints are included. Token transfers and ambiguous routes are excluded.", "Returns and matched PnL use each trade's actual quote units (SOL, USDC or USDT), before wallet-level costs. Stablecoins are not assumed to equal USD.", "A matched sell is one observation; partial unmatched disposals are excluded from win rate and average/median returns. Unobserved acquisition costs never become free inventory.", "Opening inventory, cross-quote swaps and transfers can make FIFO matching incomplete. These are observed matched-lot results, not total wallet realized PnL.", "Wallet rankings, profitability labels and statistical confidence are not established by this small, selected history."]}

def accumulation_events(histories, config):
    events, metadata = normalized_histories(histories)
    ledger, windows = QuoteLedger(), defaultdict(deque)
    signals, seen, rejected_size = [], set(), 0
    minimum = int(config.get("min_wallet_count", 3))
    covered_wallets = {h["wallet"] for h in histories if h.get("coverage_complete") is True}
    window = int(config.get("accumulation_minutes", 30)) * 60
    threshold = float(config.get("min_wallet_return_pct", 0))
    sample = int(config.get("min_closed_trades", 10))
    min_size = float(config.get("min_trade_size_usd", 0))
    for e in events:
        ts, token, wallet = e["ts"], e["token"], e["wallet"]
        score = ledger.score(wallet, ts)
        prior = windows[token]
        while prior and prior[0]["ts"] < ts - window:
            prior.popleft()
        if e["side"] == "buy" and wallet in covered_wallets and score["closed_sales"] >= sample and score["average_return_pct"] is not None and score["average_return_pct"] >= threshold:
            if min_size > 0 and (e.get("execution_price_usd") is None or e["quantity"] * e["execution_price_usd"] < min_size):
                rejected_size += 1
            else:
                prior.append(e)
                buyers = sorted({x["wallet"] for x in prior if (s := ledger.score(x["wallet"], ts))["closed_sales"] >= sample and s["average_return_pct"] is not None and s["average_return_pct"] >= threshold})
                key = (token, tuple(buyers), ts // max(1, window))
                if len(buyers) >= minimum and key not in seen:
                    seen.add(key)
                    signals.append({"token": token, "ts": ts, "wallets": buyers, "wallet_count": len(buyers), "window_seconds": ts - min(x["ts"] for x in prior if x["wallet"] in buyers), "prior_similar_events": sum(s["token"] == token and s["wallet_count"] >= minimum and s["ts"] < ts - window for s in signals), "score_basis": "prior fully matched quote-denominated sale returns, strictly before the event", "liquidity_usd": None, "eligible_for_backtest": False})
        ledger.observe(e)
    return {"kind": "REAL", "events": signals, "observed_swaps": len(events), "provenance": metadata, "size_rejections": rejected_size, "limitations": ["Research events only. No trading instruction or transaction is submitted.", "Similar-event count includes only earlier non-overlapping detections in the fetched selected sample; it is not a global historical statistic.", "Historical liquidity and USD trade sizes are unavailable from swap decoding alone. Positive USD size thresholds suppress events without USD valuations.", "Scores are based only on fully matched sales strictly before the buy. Insufficient history produces no qualified detections."]}

def build_real_dataset(payload):
    histories = payload["histories"]
    events, meta = normalized_histories(histories)
    start, end = int(payload["start_ts"]), int(payload["end_ts"])
    if not events:
        raise ValueError("No supported historical swaps were observed. A research dataset cannot be fabricated.")
    tokens = sorted({e["token"] for e in events})
    if len(tokens) > 20:
        raise ValueError("More than 20 tokens were observed. Narrow the history window.")
    missing, markets = [], payload.get("markets", {})
    def indexed(rows, fields):
        out = {}
        for row in rows:
            if not isinstance(row.get("ts"), int):
                continue
            previous = out.get(row["ts"])
            if previous is not None and any(previous.get(f) != row.get(f) for f in fields):
                raise ValueError("Conflicting historical observations share a token and timestamp. Resolve provider data before backtesting.")
            out[row["ts"]] = row
        return out
    for token in tokens:
        source = markets.get(token, {})
        prices = indexed(source.get("prices", []), ("price_usd", "source_price_ts"))
        liquidity = indexed(source.get("liquidity", []), ("liquidity_usd", "total_liquidity_usd"))
        if not prices or not liquidity:
            missing.append(f"Missing historical prices or liquidity for {token}")
        for ts in range(start, end + 1, 300):
            p, l = prices.get(ts, {}), liquidity.get(ts, {})
            events.append({"id": f"birdeye:{token}:{ts}", "type": "market", "token": token, "ts": ts, "price_usd": p.get("price_usd"), "source_price_ts": p.get("source_price_ts"), "liquidity_usd": l.get("liquidity_usd"), "total_liquidity_usd": l.get("total_liquidity_usd"), "volume_usd": None, "provider": "birdeye-historical"})
    return {"id": payload["id"], "name": payload.get("name", "Real Solana wallet study"), "kind": "REAL", "start_ts": start, "end_ts": end, "resolution_seconds": 300, "tokens": [{"mint": t, "symbol": t[:5] + "…" + t[-4:], "created_at": None} for t in tokens], "wallets": [h["wallet"] for h in histories], "events": sorted(events, key=lambda e: (e["ts"], e["id"])), "provenance": {"provider": "Helius + Birdeye" if markets else "Helius", "retrieved_at": payload["retrieved_at"], "requested_start": start, "requested_end": end, "missing_data": missing, "price_availability_lag_seconds": 300, "liquidity_field": "exit_liquidity_usd", **meta}, "limitations": ["REAL observed swaps. Missing historical prices and liquidity block performance; no synthetic data is substituted.", "Five-minute provider marks become available after their bucket closes; these are modeled fills, not exact DEX execution replay.", "Historical exit liquidity is a depth proxy, not a venue-specific quote. No current-liquidity substitution is made.", "Wallet selection and incomplete opening inventory introduce selection and survivorship bias. Token creation times are unverified."]}
