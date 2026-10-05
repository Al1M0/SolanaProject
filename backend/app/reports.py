import json
from datetime import datetime, timezone


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def report_markdown(result):
    c = result["config"]
    lines = ["# SOLANA QUANT RESEARCH LAB", f"\n**{result['dataset_kind']} DATA — {result['dataset_name']}**",
        "\n## Hypothesis", c["hypothesis"], "\n## Dataset and provenance",
        f"Dataset ID: `{result['dataset_id']}`", "```json", json.dumps(result["provenance"], indent=2), "```",
        "\n## Evaluation", f"Chronological split: {iso(result['split_ts'])}. Separate initial capital in each segment. No positions or accumulation windows cross the boundary.",
        "\n| Metric | In sample | Out of sample |", "|---|---:|---:|"]
    for key, label in (("net_return_pct", "Net return (%)"), ("gross_return_pct", "Gross return (%)"), ("trade_count", "Closed trades"), ("win_rate_pct", "Win rate (%)"), ("max_drawdown_pct", "Maximum drawdown (%)"), ("sharpe", "Daily Sharpe (annualized √365)"), ("average_trade_return_pct", "Average trade return (%)"), ("median_trade_return_pct", "Median trade return (%)"), ("profit_factor", "Profit factor"), ("costs_usd", "Execution costs (USD)")):
        values = [result[s]["metrics"].get(key) for s in ("in_sample", "out_of_sample")]
        formatted = ["Undefined" if v is None else (str(v) if isinstance(v, int) else f"{v:.6f}") for v in values]
        lines.append(f"| {label} | {formatted[0]} | {formatted[1]} |")
    lines += ["\n## Execution cost assumptions", "Network fees, DEX fees, adverse slippage and liquidity impact are configurable estimates, not a claim of exact historical execution fees.", "\n| Component (USD) | In sample | Out of sample |", "|---|---:|---:|"]
    for key, label in (("network_cost_usd", "Network"), ("dex_cost_usd", "DEX"), ("slippage_cost_usd", "Slippage"), ("liquidity_impact_cost_usd", "Liquidity impact")):
        values = [sum(t.get(key, 0) for t in result[s]["trades"]) for s in ("in_sample", "out_of_sample")]
        lines.append(f"| {label} | {values[0]:.6f} | {values[1]:.6f} |")
    lines += ["\n## Warnings"] + [f"- {s}: {w}" for s in ("in_sample", "out_of_sample") for w in result[s]["warnings"]]
    lines += ["\n## Configuration", "```json", json.dumps(c, indent=2), "```", "\n## Assumptions and limitations"]
    lines += [f"- {x}" for x in result["limitations"]]
    lines += ["- Equity uses current market marks. Fees and slippage are paid on both sides. Position budgets include entry fees; pending orders reserve cash.",
        "- Daily Sharpe uses complete UTC daily close-to-close returns, sample standard deviation, zero risk-free rate and 365-day annualization. Undefined metrics are not zero.",
        "\n## Reproducibility", f"Engine: `{result['engine_version']}`", f"Dataset SHA-256: `{result['dataset_hash']}`", f"Run fingerprint: `{result['fingerprint']}`",
        "Export the result JSON to preserve every equity observation, trade, factor snapshot, skipped execution and exact configuration."]
    return "\n".join(lines) + "\n"
