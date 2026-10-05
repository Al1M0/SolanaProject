from copy import deepcopy
import pytest
from app.analytics import normalized_histories, wallet_analytics, accumulation_events, QuoteLedger, build_real_dataset
from app.normalization import USDC, WSOL
from app.quality import assess
from app.engine import simulate
from app.factors import WalletLedger
from test_engine import fixture_dataset, config

def transaction(wallet, ts, side="buy", quantity=1, quote=10, mint="token"):
    token = {"userAccount": wallet, "mint": mint, "rawTokenAmount": {"tokenAmount": str(int(quantity * 1000000)), "decimals": 6}}
    quote_leg = {"userAccount": wallet, "mint": USDC, "rawTokenAmount": {"tokenAmount": str(int(quote * 1000000)), "decimals": 6}}
    return {"signature": f"fixture-{wallet}-{ts}-{side}", "timestamp": ts, "slot": ts, "type": "SWAP", "fee": 5000, "transactionError": None, "events": {"swap": {"tokenInputs": [quote_leg if side == "buy" else token], "tokenOutputs": [token if side == "buy" else quote_leg]}}}

def history(wallet="W", transactions=None, complete=True):
    return {"wallet": wallet, "transactions": transactions or [], "requested_start": 0, "requested_end": 3000, "coverage_complete": complete, "provider": "unit-test fixture", "retrieved_at": "fixture"}

def test_dedup_exclusions_and_no_assumed_usd_pnl():
    buy, sell = transaction("W", 1), transaction("W", 2, "sell", quote=12)
    transfer = {**buy, "type": "TRANSFER", "signature": "transfer"}
    result = wallet_analytics([history(transactions=[buy, buy, sell, transfer])])
    wallet = result["wallets"][0]
    assert wallet["observed_trades"] == 2 and wallet["closed_sales"] == 1
    assert wallet["average_return_pct"] == pytest.approx(20)
    assert wallet["observed_matched_pnl_by_quote"] == {"USDC": 2}
    assert wallet["realized_pnl_usd"] is None
    assert wallet["evidence_status"] == "Insufficient historical data"
    assert result["provenance"]["rejected"]["not_supported_swap"] == 1

def test_unknown_inventory_partial_sale_and_cross_quote_are_not_profitability_evidence():
    result = wallet_analytics([history(transactions=[transaction("W", 1, "sell"), transaction("W", 2), transaction("W", 3, "sell", quantity=2, quote=30)])])
    wallet = result["wallets"][0]
    assert wallet["unmatched_sales"] == 2 and wallet["partial_matched_sales"] == 1
    assert wallet["closed_sales"] == 0 and wallet["win_rate_pct"] is None and wallet["median_return_pct"] is None
    ledger = QuoteLedger()
    ledger.observe({"wallet": "W", "token": "T", "side": "buy", "quantity": 1, "quote_quantity": 10, "quote_mint": USDC, "ts": 1})
    ledger.observe({"wallet": "W", "token": "T", "side": "sell", "quantity": 1, "quote_quantity": 2, "quote_mint": WSOL, "ts": 2})
    assert ledger.score("W", 3)["closed_sales"] == 0

def prior(wallet, sale_ts=2):
    return history(wallet, [transaction(wallet, 1), transaction(wallet, sale_ts, "sell", quote=12), transaction(wallet, 600, "buy")])

def test_unique_wallet_cluster_uses_strictly_prior_sales_and_expiring_window():
    c = {"min_closed_trades": 1, "min_wallet_count": 3, "accumulation_minutes": 10}
    histories = [prior(w) for w in ("A", "B", "C")]
    result = accumulation_events(histories, c)
    assert len(result["events"]) == 1 and result["events"][0]["wallet_count"] == 3
    future = deepcopy(histories)
    for h in future:
        h["transactions"][1]["timestamp"] = 1000
    assert accumulation_events(future, c)["events"] == []
    same = deepcopy(histories)
    for h in same:
        h["transactions"][1]["timestamp"] = 600
    assert accumulation_events(same, c)["events"] == []
    incomplete = deepcopy(histories); incomplete[0]["coverage_complete"] = False
    assert accumulation_events(incomplete, c)["events"] == []

def test_positive_usd_minimum_does_not_assume_stablecoins_are_dollars():
    histories = [prior(w) for w in ("A", "B", "C")]
    result = accumulation_events(histories, {"min_closed_trades": 1, "min_wallet_count": 3, "min_trade_size_usd": 1})
    assert not result["events"] and result["size_rejections"] == 3

def test_real_import_missing_liquidity_blocks_engine_and_no_current_substitution():
    h = history(transactions=[transaction("W", 300)])
    h.update(requested_start=0, requested_end=1200)
    d = build_real_dataset({"id": "unit_test_real", "histories": [h], "start_ts": 0, "end_ts": 1200, "retrieved_at": "unit-test fixture", "markets": {"token": {"prices": [{"ts": ts, "price_usd": 1} for ts in range(0, 1201, 300)], "liquidity": []}}})
    assert d["kind"] == "REAL" and not assess(d)["performance_ready"]
    assert all(e["liquidity_usd"] is None for e in d["events"] if e["type"] == "market")

def test_minimum_trade_size_filters_buy_signal_but_keeps_prior_ledger_evidence():
    small = simulate(fixture_dataset(), config(min_trade_size_usd=1051), 600, 3000, "test")
    assert small["signals"] == []
    eligible = simulate(fixture_dataset(), config(min_trade_size_usd=1050), 600, 3000, "test")
    assert len(eligible["trades"]) == 1

def test_liquidity_impact_reduces_net_and_cost_breakdown_reconciles():
    d = fixture_dataset()
    base = simulate(d, config(fee_bps=30, slippage_bps=20, fixed_fee_usd=.01), 600, 3000, "test")
    impacted = simulate(d, config(fee_bps=30, slippage_bps=20, fixed_fee_usd=.01, liquidity_impact_bps_per_pct=100), 600, 3000, "test")
    t = impacted["trades"][0]
    assert impacted["metrics"]["net_return_pct"] < base["metrics"]["net_return_pct"]
    assert t["liquidity_impact_cost_usd"] > 0
    assert sum(t[k] for k in ("network_cost_usd", "dex_cost_usd", "slippage_cost_usd", "liquidity_impact_cost_usd")) == pytest.approx(t["costs_usd"])
    assert impacted["metrics"]["median_trade_return_pct"] == t["return_pct"]

def test_partial_unknown_inventory_cannot_qualify_backtest_wallet_score():
    ledger = WalletLedger()
    ledger.observe({"wallet": "W", "token": "T", "side": "buy", "quantity": 1, "ts": 1}, 10)
    ledger.observe({"wallet": "W", "token": "T", "side": "sell", "quantity": 2, "ts": 2}, 15)
    assert ledger.score("W", 3) == {"closed_trades": 0, "return_pct": None}

def test_conflicting_price_history_is_not_silently_overwritten():
    h = history(transactions=[transaction("W", 300)])
    with pytest.raises(ValueError, match="Conflicting historical"):
        build_real_dataset({"id": "fixture", "histories": [h], "start_ts": 0, "end_ts": 1200, "retrieved_at": "fixture", "markets": {"token": {"prices": [{"ts": 300, "price_usd": 1}, {"ts": 300, "price_usd": 2}]}}})
