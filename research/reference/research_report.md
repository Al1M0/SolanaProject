# Hypothesis audit

Experiment: `exp_4514bc9bb0270736afa3555d`
Dataset: **SYNTHETIC**
Hypothesis: When multiple previously profitable wallets accumulate a token, subsequent returns may exceed execution costs.
Dataset SHA-256: `d1472d81d69983de87dad530d89bf0e1f108552086da79719cae74f71d09107d`
Frozen manifest SHA-256: `cd6d52b8b867e538113b8eef33fd9d67143777ee4af8d8bc15ba4c270536aa6a`
Engine: `source-sha256:697441c3e80d5740405e38f36f16b7b6288b30a269b236d8fe2dfbf9a09d02c5`

Historical holdout may already be known from raw data. This lock protects the stored snapshot, not secrecy or absence of human look-ahead.

## Training

| Portfolio | Gross % | Net % | Costs USD | Trades | Exposure % | Turnover | Failed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strategy | -4.5303 | -12.7829 | 825.2550 | 83 | 7.7877 | 16.4719 | 2 |
| buy_and_hold | -4.2757 | -4.6532 | 37.7451 | 4 | 39.1592 | 0.7533 | 0 |
| momentum | 1.0640 | -20.8755 | 2193.9512 | 220 | 11.1212 | 43.7910 | 3 |

- Strategy net result at or below Fixed allocation buy-and-hold by -8.13 percentage points in this period; exposure and turnover differ.
- Strategy net result above Simple momentum by +8.09 percentage points in this period; exposure and turnover differ.
- This comparison does not establish proven alpha or future profitability.

- SYNTHETIC DATA: every price, wallet, liquidity observation and transaction is simulated. Returns are not evidence of real Solana alpha.
- Four simulated tokens and twelve wallets are an engineering test universe, not a representative market sample.
- Five-minute observations do not reproduce intrabar execution or sub-minute accumulation.
- The wallet/token universe is supplied before the experiment but may have been chosen with hindsight. Full-period token discovery, surviving tokens and public wallet rankings can create universe-selection bias. Benchmarks do not remove it.
- Same dates, capital, token universe, observation availability, delay, liquidity cap and per-side cost assumptions; activity and exposure differ by design. Return differences alone do not measure skill.
- Gross returns remove costs from the same executed quantities, not a separately re-sized zero-cost portfolio. Liquidity and fills are models, not AMM replay; MEV and actual failed-chain fees are not modeled.
- Historical holdouts are not guaranteed unseen: the user may already possess the raw data. Repeated test-period trials contaminate the holdout.
- Wallet eligibility is calculated from observed matched lots within the selected token universe; it is not lifetime wallet profitability.
- Small samples are inconclusive. No proven alpha, p-values, confidence scores or confidence intervals are provided. Walk-forward with purge/embargo is future work.

## Historical holdout

| Portfolio | Gross % | Net % | Costs USD | Trades | Exposure % | Turnover | Failed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strategy | 1.2818 | -1.9150 | 319.6830 | 32 | 6.5968 | 6.3808 | 0 |
| buy_and_hold | 4.6639 | 4.2418 | 42.2095 | 4 | 42.1468 | 0.8426 | 0 |
| momentum | 1.4937 | -8.8826 | 1037.6353 | 104 | 11.5245 | 20.7111 | 2 |

- Costs erase the strategy's observed gross return in this period.
- Strategy net result at or below Fixed allocation buy-and-hold by -6.16 percentage points in this period; exposure and turnover differ.
- Strategy net result above Simple momentum by +6.97 percentage points in this period; exposure and turnover differ.
- This comparison does not establish proven alpha or future profitability.

- SYNTHETIC DATA: every price, wallet, liquidity observation and transaction is simulated. Returns are not evidence of real Solana alpha.
- Four simulated tokens and twelve wallets are an engineering test universe, not a representative market sample.
- Five-minute observations do not reproduce intrabar execution or sub-minute accumulation.
- The wallet/token universe is supplied before the experiment but may have been chosen with hindsight. Full-period token discovery, surviving tokens and public wallet rankings can create universe-selection bias. Benchmarks do not remove it.
- Same dates, capital, token universe, observation availability, delay, liquidity cap and per-side cost assumptions; activity and exposure differ by design. Return differences alone do not measure skill.
- Gross returns remove costs from the same executed quantities, not a separately re-sized zero-cost portfolio. Liquidity and fills are models, not AMM replay; MEV and actual failed-chain fees are not modeled.
- Historical holdouts are not guaranteed unseen: the user may already possess the raw data. Repeated test-period trials contaminate the holdout.
- Wallet eligibility is calculated from observed matched lots within the selected token universe; it is not lifetime wallet profitability.
- Small samples are inconclusive. No proven alpha, p-values, confidence scores or confidence intervals are provided. Walk-forward with purge/embargo is future work.

## Sensitivity
Training-only pre-specified grid. All rows retained; no holdout optimization.
```json
{
  "design": {
    "design": "Seven pre-specified one-at-a-time rows; base plus low/high fees, delay and unique-wallet threshold. Training only; no best-row selection.",
    "fees": "base / 2, min(1000, base * 2 + 10)",
    "delays_minutes": "max(0, base - 5), min(1440, base + 5)",
    "unique_buyers": "max(1, base - 1), min(100, base + 1)"
  },
  "rows": [
    {
      "row": "base",
      "changes": {},
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -4.530309721294634,
        "net_return_pct": -12.78285993022057,
        "gross_return_pct": -4.530309721294634,
        "win_rate_pct": 33.734939759036145,
        "max_drawdown_pct": 12.78285993022057,
        "sharpe": -47.97688337349583,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 83,
        "average_trade_return_pct": -1.5401036060506699,
        "median_trade_return_pct": -1.3490392584501025,
        "profit_factor": 0.2481036658992238,
        "profit_factor_reason": null,
        "costs_usd": 825.2550208925918,
        "ending_equity_usd": 8721.714006977943
      },
      "fingerprint": "8ba0f0260484ba45206ece154e199f4f7505a27d4fbd2e404dc77ac42bf29f3a"
    },
    {
      "row": "fee_low",
      "changes": {
        "fee_bps": 15.0
      },
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -4.537095007946612,
        "net_return_pct": -10.327489505206922,
        "gross_return_pct": -4.537095007946612,
        "win_rate_pct": 33.734939759036145,
        "max_drawdown_pct": 10.327489505206922,
        "sharpe": -36.00776844247389,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 83,
        "average_trade_return_pct": -1.2442758440008337,
        "median_trade_return_pct": -1.0526374396891585,
        "profit_factor": 0.32935785305393506,
        "profit_factor_reason": null,
        "costs_usd": 579.0394497260315,
        "ending_equity_usd": 8967.251049479308
      },
      "fingerprint": "4538fc46ce9e020ecfe2c413a28da31c96ca058eaf715b71fba3750554f5dca1"
    },
    {
      "row": "fee_high",
      "changes": {
        "fee_bps": 70.0
      },
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -4.512314449313326,
        "net_return_pct": -19.29475262972755,
        "gross_return_pct": -4.512314449313326,
        "win_rate_pct": 20.481927710843372,
        "max_drawdown_pct": 19.29475262972755,
        "sharpe": -74.53486043484065,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 83,
        "average_trade_return_pct": -2.3246689915334366,
        "median_trade_return_pct": -2.135127100857562,
        "profit_factor": 0.1147628886127932,
        "profit_factor_reason": null,
        "costs_usd": 1478.243818041419,
        "ending_equity_usd": 8070.524737027245
      },
      "fingerprint": "453dd720303686480e4e41e034cec43993ed54e5e1d97e3968a7429942ad25ed"
    },
    {
      "row": "delay_low",
      "changes": {
        "entry_delay_minutes": 0
      },
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -4.530309721294634,
        "net_return_pct": -12.78285993022057,
        "gross_return_pct": -4.530309721294634,
        "win_rate_pct": 33.734939759036145,
        "max_drawdown_pct": 12.78285993022057,
        "sharpe": -47.97688337349583,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 83,
        "average_trade_return_pct": -1.5401036060506699,
        "median_trade_return_pct": -1.3490392584501025,
        "profit_factor": 0.2481036658992238,
        "profit_factor_reason": null,
        "costs_usd": 825.2550208925918,
        "ending_equity_usd": 8721.714006977943
      },
      "fingerprint": "6598443e998df4242a5c53c512150218caf34b89f3eaf6215b4461a5798af40f"
    },
    {
      "row": "delay_high",
      "changes": {
        "entry_delay_minutes": 10
      },
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -6.047797229949703,
        "net_return_pct": -14.093367309253157,
        "gross_return_pct": -6.047797229949703,
        "win_rate_pct": 29.629629629629626,
        "max_drawdown_pct": 14.093367309253157,
        "sharpe": -87.93789212645765,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 81,
        "average_trade_return_pct": -1.7399218900312587,
        "median_trade_return_pct": -1.8910145667888172,
        "profit_factor": 0.21714117563314195,
        "profit_factor_reason": null,
        "costs_usd": 804.55700793035,
        "ending_equity_usd": 8590.663269074685
      },
      "fingerprint": "e0afe3db50c94f86582858df8cfce3c8b249dcfafde7c4e46250f994f615bb1f"
    },
    {
      "row": "buyers_low",
      "changes": {
        "min_wallet_count": 2
      },
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -2.7099229656165735,
        "net_return_pct": -16.25571180661154,
        "gross_return_pct": -2.7099229656165735,
        "win_rate_pct": 36.76470588235294,
        "max_drawdown_pct": 16.922107573983027,
        "sharpe": -41.85542622378859,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 136,
        "average_trade_return_pct": -1.1952729269567284,
        "median_trade_return_pct": -1.2836748586922737,
        "profit_factor": 0.4077905842791578,
        "profit_factor_reason": null,
        "costs_usd": 1354.578884099493,
        "ending_equity_usd": 8374.428819338846
      },
      "fingerprint": "d2a52f821ad86ab0e3d8e847e67aa1344c1cedf7a6685b8a19d94e39086de19f"
    },
    {
      "row": "buyers_high",
      "changes": {
        "min_wallet_count": 4
      },
      "phase": "training",
      "end_ts": 1768098000,
      "metrics": {
        "total_return_pct": -1.2737159178319413,
        "net_return_pct": -4.557484631107478,
        "gross_return_pct": -1.2737159178319413,
        "win_rate_pct": 39.39393939393939,
        "max_drawdown_pct": 4.557484631107478,
        "sharpe": -16.977990995262275,
        "sharpe_observations": 8,
        "sharpe_reason": null,
        "trade_count": 33,
        "average_trade_return_pct": -1.3810559488204508,
        "median_trade_return_pct": -0.7412830405055957,
        "profit_factor": 0.34455567754264405,
        "profit_factor_reason": null,
        "costs_usd": 328.376871327555,
        "ending_equity_usd": 9544.251536889253
      },
      "fingerprint": "f93cbe8dc79031817158e6100ce35124062d59da7b78cea8d5d25ac171bf0551"
    }
  ],
  "selection": "No automated selection; freeze the user's current configuration, not the best row"
}
```

## Benchmark definitions
{
  "buy_and_hold": {
    "name": "Fixed allocation buy-and-hold",
    "allocation": "Each token receives min(strategy position budget, 90% of starting capital / selected token count). Unallocated, ineligible or failed allocations remain cash; no redistribution.",
    "rule": "Decide at the first evaluation bar using available liquidity; buy on the first later bar after the shared delay; hold until segment end. No stops, targets or rebalancing."
  },
  "momentum": {
    "name": "Simple momentum",
    "allocation": "Same fixed allocation per token as buy-and-hold; no leverage or redistribution.",
    "rule": "At segment start and every 60 minutes, buy if the available price is at least 1% above the available price 60 minutes earlier. Hold 60 minutes; no stops or targets. No entry while invested or pending."
  }
}
