# Research methodology

## Information set

Events are sorted by timestamp, market-before-swap type, slot and identity. A market snapshot is available at its declared timestamp. Wallet profitability is computed from observed matched FIFO acquisitions and sales with `sale_timestamp < signal_timestamp`. Same-timestamp sales cannot qualify a wallet. The engine never computes a final wallet leaderboard to choose historical wallets.

Selected wallet IDs define a fixed research universe. This does not cure selection or survivorship bias in the supplied universe. Wallet ROI is aggregate proceeds / matched cost − 1, before wallet-specific costs. Unmatched sells never count as free profit. Sales with a partly unknown acquisition cost do not qualify wallet scores, while known partial-lot disposals remain matchable. In real datasets, missing executed USD prices are valued only from available lagged market marks, explicitly as a proxy. Stablecoin quotes are not assumed equal to USD.

## Factors

- **Accumulation:** count distinct eligible selected buyers in an inclusive trailing time window. Repeat buys add volume, not wallet count. Wallet eligibility is rechecked at each potential signal.
- **Profitability:** gross FIFO realized return and a minimum number of prior matched sale observations.
- **Volume:** USD value of those eligible wallet buys, not the token's entire market turnover.
- **Liquidity:** historical depth at the signal and execution observations. The real adapter uses historical `exit_liquidity_usd`; aggregate depth is not an executable venue quote.
- **Age:** signal time minus verified creation time. A positive filter is prohibited for unknown creation times.
- **Momentum:** available price relative to the last observed price at or before the lookback boundary. A threshold of −100 disables the filter; missing required momentum rejects the signal.

## Orders and accounting

There is at most one open or pending position per token. Signal-time cash checks reserve complete position budgets for pending orders. Entries execute at the first later market observation at or after `signal + entry_delay`. Even a zero delay cannot fill on the signal observation.

For budget B, proportional per-side fee f, fixed per-side fee F, adverse slippage s and entry mark P:

```text
entry_notional = (B - F) / (1 + f)
entry_price   = P * (1 + s)
quantity      = entry_notional / entry_price
entry_fee     = entry_notional * f + F
cash          = cash - B
exit_price    = exit_mark * (1 - s)
exit_proceeds = quantity * exit_price
exit_fee      = exit_proceeds * f + F
cash          = cash + exit_proceeds - exit_fee
net_PnL       = exit_proceeds - exit_fee - B
gross_PnL     = quantity * (exit_mark - entry_mark)
total_costs   = gross_PnL - net_PnL
```

The liquidity participation cap is checked again at each fill. A failed entry is logged and canceled. Failed exits remain open and retry on later observations. Stops/targets are observed using the current mark versus the entry fill, then execute on the next market observation, allowing adverse gaps. A known holding deadline executes on the first eligible observation. Segment-end liquidation uses the final known scheduled observation. Inability to liquidate blocks that segment's performance metrics.

Equity is cash plus open quantity at current market marks. Marked equity does not pre-charge hypothetical exit fees; those are charged on closing. Gross equity uses the same actual position quantities/timing, removing costs, rather than a separate zero-cost strategy with different sizing.

## Chronological validation

Warmup is excluded from trading and used to accumulate past wallet evidence. The remaining time grid splits chronologically by the configured training fraction. The in-sample segment ends one observation before test begins. Each segment starts with the same fresh initial capital and liquidates at its end. Pending orders and rolling accumulation do not cross the boundary. Previously observed wallet information may be reused in the test period because it is already public at that time.

There is no automatic parameter fitting. The split is an evaluation protocol, not proof of unbiased model selection. Repeatedly examining and tuning on the holdout invalidates its interpretation as unseen evidence. Walk-forward nested validation and multiple-testing correction are not implemented.

## Metrics and limitations

- Net/gross returns: ending portfolio value / initial capital − 1.
- Maximum drawdown: largest decline from the preceding net marked-equity peak.
- Win rate: proportion of completed trades with strictly positive net P&L; zero-return trades are not wins.
- Average/median trade return: arithmetic mean/median of net P&L / original position budget.
- Profit factor: summed positive net P&L / absolute summed negative net P&L. No losses means undefined, not fabricated infinity.
- Sharpe: mean complete UTC daily return / sample standard deviation × √365, with zero risk-free rate. At least two daily returns and positive variance are required. A final partial day is excluded; short samples carry an explicit warning.
- Zero trades: portfolio return can be zero; win rate, average trade return and profit factor remain undefined. No NaN/Infinity is serialized.

Missing required market bars, prices, liquidity or incomplete wallet paging blocks a run before performance calculations. None are forward-filled. The engine is intended for small curated datasets; there is a 250,000-event limit. Numerical accounting uses double precision with test tolerances, not settlement-grade fixed-point arithmetic.

## Liquidity impact and wallet evidence

The configurable impact coefficient adds linear adverse impact: `impact_bps = liquidity_impact_bps_per_pct × (trade_value_usd / historical_liquidity_usd × 100)`. Entry/exit prices include this impact as well as slippage. Each closed trade separates network, DEX, slippage and liquidity-impact costs; their sum reconciles to gross minus net PnL. This is an assumption over observed historical depth, not an AMM execution replay.

Wallet research/live scores use the arithmetic mean of fully matched quote-denominated sale returns. PnL is shown in actual SOL/USDC/USDT units; no stablecoin-to-USD assumption or total wallet USD PnL is made. Backtest wallet scores use aggregate modeled USD FIFO ROI using observed lagged market marks. These distinct bases are labeled and are both evaluated strictly before the signal. Neither establishes a wallet's lifetime profitability.

Live current-liquidity observations apply at polling time. Their values cannot qualify a historical backtest. Positive USD buy-size filters require historical USD valuations; decoded-only swaps without them do not qualify. The live holding-period setting records a proposed study horizon; realized outcomes must be evaluated through historical datasets and Strategy lab.

## Hypothesis audit and benchmarks — engine 1.2.0

The Audit route runs the selected token universe through the same `simulate` fill/accounting path for all three portfolios. The shared dates, capital, lagged price/liquidity rules, entry delay, liquidity participation cap and per-side costs are fixed for the phase. Wallet scores use observed matched lots inside that selected token universe.

Buy-and-hold fixes each token's budget at `min(strategy position_size_usd, 0.9 × initial_capital_usd / token_count)` before evaluation. Decide on the phase's first bar using available eligibility; fill only on a later bar after the configured delay; hold to the phase end. Ineligible or failed allocations remain cash. No rebalancing, stops, targets or hindsight ranking. With defaults, four tokens receive $1,000 each and the remainder stays cash.

Momentum uses the same fixed budgets. At phase start and each following 60-minute boundary, buy if the available price return versus the available observation 60 minutes earlier is at least +1%. Hold for 60 minutes with no stops/targets; no overlapping or pending position in the same token. Entry/exit and segment-end liquidation use the shared model. The rule is pre-specified, not tuned to the reference returns.

Time-weighted exposure integrates marked invested value / net equity over the phase. Round-trip turnover is the sum of executed entry/exit notionals / starting capital. Failed execution count includes logged exclusions and unfilled orders, not failed on-chain submissions. These differences are displayed so activity is not misrepresented as skill.

Training/sensitivity pass only events at or before training end to the simulator. A seven-row one-at-a-time grid reports base and lower/higher fees, delays and buyer count; no automatic winner is selected. A manifest binds the full immutable dataset, exact configuration/universe/split, benchmark definitions, seed and the engine source-content revision. Each attempt is separately persisted, including runtime failure.

Freeze requires completed training. The database protects manifest fields and the frozen hash from mutation; the API permits one holdout lifecycle transition per attempt. New parameters create a new attempt. This prevents accidental in-workflow tuning, not knowledge of raw historical data, legacy exploratory runs, administrator edits or experimentation in other workspaces. No prospective untouched data claim is made.

Walk-forward, purge/embargo for overlapping holdings/labels, multiple-testing inference and prospective paper runs remain future work. No p-values, confidence intervals or confidence scores are added. The inherited Sharpe is descriptive, with warnings, and is deliberately not emphasized in the audit comparison.
