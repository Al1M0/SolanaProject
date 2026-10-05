import copy
import pytest
from app.audit import run_audit
from app.demo import generate_demo
from app.domain import ResearchDataError

def test_benchmarks_share_dates_cost_accounting_and_chronology():
    d = generate_demo(days=4)
    a = run_audit(d, {}, phase="training")
    for key, s in a["results"].items():
        assert (s["start_ts"], s["end_ts"]) == (a["split"]["training_start"], a["split"]["training_end"])
        for t in s["trades"]:
            assert s["start_ts"] <= t["signal_ts"] < t["entry_ts"] <= t["exit_ts"] <= s["end_ts"]
            assert t["gross_pnl_usd"] - t["net_pnl_usd"] == pytest.approx(t["costs_usd"])
            assert sum(t[k] for k in ("network_cost_usd", "dex_cost_usd", "slippage_cost_usd", "liquidity_impact_cost_usd")) == pytest.approx(t["costs_usd"])
        assert s["metrics"]["ending_equity_usd"] == pytest.approx(10000 + sum(t["net_pnl_usd"] for t in s["trades"]))
        assert s["activity"]["round_trip_turnover_x"] >= 0
    assert all(t["reason"] == "segment_end" for t in a["results"]["buy_and_hold"]["trades"])

def test_future_prices_and_swaps_cannot_change_training_or_momentum():
    d = generate_demo(days=4)
    a = run_audit(d, {})
    changed = copy.deepcopy(d)
    for e in changed["events"]:
        if e["ts"] >= a["split"]["holdout_start"]:
            if e["type"] == "market":
                e["price_usd"] *= 100
                e["liquidity_usd"] = None
            else:
                e["quantity"] *= 100
    b = run_audit(changed, {})
    assert a["results"] == b["results"]
    assert a["fingerprint"] == b["fingerprint"]
    with pytest.raises(ResearchDataError, match="blocked"):
        run_audit(changed, {}, phase="holdout")

def test_missing_required_training_data_and_unknown_universe_block():
    d = generate_demo(days=4)
    with pytest.raises(ResearchDataError, match="declared token"):
        run_audit(d, {}, ["unknown"])
    next(e for e in d["events"] if e["type"] == "market")["price_usd"] = None
    with pytest.raises(ResearchDataError, match="blocked"):
        run_audit(d, {})

def test_no_future_token_ranking_and_ineligible_fixed_allocations_remain_cash():
    d = generate_demo(days=4)
    for e in d["events"]:
        if e["type"] == "market":
            e["liquidity_usd"] = 1
    a = run_audit(d, {})
    assert not a["results"]["buy_and_hold"]["trades"]
    assert a["results"]["buy_and_hold"]["metrics"]["ending_equity_usd"] == 10000
    assert a["results"]["buy_and_hold"]["skipped"]

def test_momentum_decisions_use_available_hour_old_prices_and_no_future_selection():
    d=generate_demo(days=4)
    audit=run_audit(d,{})
    markets={(e['token'],e['ts']):e['price_usd'] for e in d['events'] if e['type']=='market'}
    for signal in audit['results']['momentum']['signals']:
        ts,token=signal['ts'],signal['token']
        assert (ts-audit['split']['training_start'])%3600==0
        expected=(markets[token,ts]/markets[token,ts-3600]-1)*100
        assert expected>=1 and signal['factors']['momentum_pct']==pytest.approx(expected)


def test_real_price_availability_must_be_documented_and_cannot_be_future():
    from app.quality import assess
    d=generate_demo(days=4)
    # Validation fixture only, never presented as a genuine study.
    d['kind']='REAL'
    assert not assess(d)['performance_ready']
    for e in d['events']:
        if e['type']=='market':e['source_price_ts']=e['ts']-300
    assert assess(d)['performance_ready']
    next(e for e in d['events'] if e['type']=='market')['source_price_ts']+=300
    assert not assess(d)['performance_ready']
