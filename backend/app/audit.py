"""Transparent comparisons. Portable, deterministic; no fitting or significance claims."""
from dataclasses import replace
from .domain import StrategyConfig, ResearchDataError
from .engine import digest, simulate, ENGINE_VERSION
from .quality import assess

BENCHMARKS = {
    "buy_and_hold": {"name": "Fixed allocation buy-and-hold", "allocation": "Each token receives min(strategy position budget, 90% of starting capital / selected token count). Unallocated, ineligible or failed allocations remain cash; no redistribution.",
        "rule": "Decide at the first evaluation bar using available liquidity; buy on the first later bar after the shared delay; hold until segment end. No stops, targets or rebalancing."},
    "momentum": {"name": "Simple momentum", "allocation": "Same fixed allocation per token as buy-and-hold; no leverage or redistribution.",
        "rule": "At segment start and every 60 minutes, buy if the available price is at least 1% above the available price 60 minutes earlier. Hold 60 minutes; no stops or targets. No entry while invested or pending."}
}
COMMON_LIMITATIONS = [
    "The wallet/token universe is supplied before the experiment but may have been chosen with hindsight. Full-period token discovery, surviving tokens and public wallet rankings can create universe-selection bias. Benchmarks do not remove it.",
    "Same dates, capital, token universe, observation availability, delay, liquidity cap and per-side cost assumptions; activity and exposure differ by design. Return differences alone do not measure skill.",
    "Gross returns remove costs from the same executed quantities, not a separately re-sized zero-cost portfolio. Liquidity and fills are models, not AMM replay; MEV and actual failed-chain fees are not modeled.",
    "Historical holdouts are not guaranteed unseen: the user may already possess the raw data. Repeated test-period trials contaminate the holdout.",
    "Wallet eligibility is calculated from observed matched lots within the selected token universe; it is not lifetime wallet profitability.",
    "Small samples are inconclusive. No proven alpha, p-values, confidence scores or confidence intervals are provided. Walk-forward with purge/embargo is future work."
]

def bounds(dataset, config):
    step = dataset["resolution_seconds"]
    first = dataset["start_ts"] + ((config.warmup_hours * 3600 + step - 1) // step) * step
    count = (dataset["end_ts"] - first) // step + 1
    if count < 8:
        raise ResearchDataError("Insufficient observations after warmup for chronological training and holdout")
    split = first + int(count * config.train_fraction) * step
    return {"warmup_start": dataset["start_ts"], "training_start": first, "training_end": split - step, "holdout_start": split, "holdout_end": dataset["end_ts"]}

def canonical_dataset(dataset):
    # Summaries may carry derived/storage fields; they are not observations.
    return {k: v for k, v in dataset.items() if k not in ("quality", "content_hash", "created_at")}

def select_universe(dataset, tokens):
    tokens = sorted(set(tokens or [t["mint"] for t in dataset["tokens"]]))
    if not tokens or not set(tokens) <= {t["mint"] for t in dataset["tokens"]}:
        raise ResearchDataError("Select at least one declared token; the universe is fixed before evaluation")
    return {**canonical_dataset(dataset), "tokens": [t for t in dataset["tokens"] if t["mint"] in tokens], "events": [e for e in dataset["events"] if e["token"] in tokens]}, tokens

def activity(segment, capital):
    curve, trades = segment["equity_curve"], segment["trades"]
    span = max(1, segment["end_ts"] - segment["start_ts"])
    weighted = sum(max(0, curve[i+1]["ts"] - row["ts"]) * max(0, row["net_equity"] - row["cash"]) / row["net_equity"] for i, row in enumerate(curve[:-1]) if row["net_equity"] > 0)
    return {"time_weighted_exposure_pct": weighted / span * 100,
        "round_trip_turnover_x": sum(t["quantity"] * (t["entry_price"] + t["exit_price"]) for t in trades) / capital,
        "trade_count": len(trades), "signal_count": len(segment["signals"]), "failed_execution_count": len(segment["skipped"]),
        "cost_breakdown_usd": {key: sum(t.get(key, 0) for t in trades) for key in ("network_cost_usd", "dex_cost_usd", "slippage_cost_usd", "liquidity_impact_cost_usd")}}

def findings(results):
    strategy = results["strategy"]["metrics"]
    messages = []
    if any(not row["valid"] for row in results.values()):
        return ["Comparison blocked: at least one portfolio could not liquidate. Inspect failed executions."]
    gross, net = strategy["gross_return_pct"], strategy["net_return_pct"]
    if gross is not None and gross > 0 and net <= 0:
        messages.append("Costs erase the strategy's observed gross return in this period.")
    if strategy["trade_count"] < 30:
        messages.append("Insufficient independent evidence: fewer than 30 closed strategy trades. This threshold is a sample warning, not a statistical test.")
    for key, definition in BENCHMARKS.items():
        baseline = results[key]["metrics"]["net_return_pct"]
        if net is not None and baseline is not None:
            messages.append(f"Strategy net result {'above' if net > baseline else 'at or below'} {definition['name']} by {net-baseline:+.2f} percentage points in this period; exposure and turnover differ.")
    messages.append("This comparison does not establish proven alpha or future profitability.")
    return messages

def run_audit(dataset, config_dict, token_ids=None, phase="training", progress=None):
    if phase not in ("training", "holdout"):
        raise ValueError("Audit phase must be training or holdout")
    c = StrategyConfig.from_dict(config_dict)
    data, tokens = select_universe(dataset, token_ids)
    split = bounds(data, c)
    a, b = (split["training_start"], split["training_end"]) if phase == "training" else (split["holdout_start"], split["holdout_end"])
    visible = {**data, "end_ts": b, "events": [e for e in data["events"] if e["ts"] <= b]}
    quality = assess(visible)
    if not quality["performance_ready"]:
        raise ResearchDataError("Performance blocked: " + "; ".join(quality["issues"]))
    if len(data["events"]) > 250000:
        raise ResearchDataError("MVP limit: 250,000 events")
    if c.wallet_ids and not set(c.wallet_ids) <= set(data["wallets"]):
        raise ResearchDataError("Selected wallet does not exist in dataset")
    if c.min_token_age_hours and any(t.get("created_at") is None for t in data["tokens"]):
        raise ResearchDataError("Token-age filtering requires verified creation times")
    allocation = min(c.position_size_usd, c.initial_capital_usd * .9 / len(tokens))
    if allocation <= c.fixed_fee_usd:
        raise ResearchDataError("Benchmark allocation cannot cover the shared fixed entry fee")
    benchmark_config = replace(c, position_size_usd=allocation)
    results = {}
    for i, key in enumerate(("strategy", "buy_and_hold", "momentum")):
        cfg = c if key == "strategy" else benchmark_config
        segment = simulate(visible, cfg, a, b, phase, policy=None if key == "strategy" else key)
        segment["activity"] = activity(segment, c.initial_capital_usd)
        results[key] = segment
        if progress:
            progress((i+1)*100//3)
    return {"phase": phase, "engine_version": ENGINE_VERSION, "dataset_kind": data["kind"], "dataset_id": data["id"],
        "dataset_hash": digest(canonical_dataset(dataset)), "fingerprint": digest({"engine": ENGINE_VERSION, "dataset": digest(visible), "config": c.to_dict(), "tokens": tokens, "phase": phase, "benchmarks": BENCHMARKS}),
        "split": split, "quality": quality, "tokens": tokens, "benchmarks": BENCHMARKS, "benchmark_allocation_usd": allocation,
        "results": results, "findings": findings(results), "limitations": data.get("limitations", []) + COMMON_LIMITATIONS}
