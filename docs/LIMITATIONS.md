# Known limitations and next priorities

## Implemented boundary

The MVP implements one long-only Smart Money Accumulation entry rule with six configurable factors. All performance is event-driven. It is not a strategy optimizer, autonomous trader, or predictor. The included fourteen-day simulation exists to test the system, not establish alpha.

The hosted application includes a server API for mainnet observations, market charts and signed-wallet sessions. Synthetic and imported REAL research datasets run through the same Python engine as FastAPI in a browser worker. Hosted detailed research datasets/results remain device-local; immutable audit manifests/lifecycle hashes and signed-owner wallet observations persist in D1. PostgreSQL research persistence and asynchronous real ingestion run in the downloadable native stack. Public market responses were verified separately; authorized server keys subsequently verified Helius history and Birdeye historical price retrieval. Historical exit liquidity is still denied, and required prices have gaps, so REAL performance remains blocked. Docker/PostgreSQL execution was unavailable; those paths are supplied but not runtime verified. SQLite migrations and the full native API flow were verified.

## Research limits

- Short sample, single chronological holdout, no significance testing, walk-forward optimization or multiple-hypothesis correction.
- Fixed supplied wallet/token universe may have selection/survivorship bias. No historical universe reconstruction.
- Gross observed FIFO wallet evidence; transfers, missing initial inventory, wallet-level costs and unsupported swaps are not reconstructed.
- Five-minute observations, discrete stops/targets, configurable per-side slippage, network/DEX fee and linear liquidity-impact assumptions, and aggregate historical liquidity cap. No AMM reserve replay, venue routing, order book, MEV, chain failures, compute-unit dynamics, transfer fees or Token-2022 extensions.
- No shorts, margin, leverage, limit orders, portfolio optimization or automatic position sizing.
- Missing required data blocks the evaluated phase instead of providing subtly biased partial performance; the audit can inspect valid training even when later holdout observations are incomplete. A future valid-interval research mode needs its own methodology and tests.
- Current real ingestion intentionally does not verify token creation times. Age filtering on unknown dates is blocked.
- Sharpe ratios from a few daily observations are mathematically defined but highly uncertain; the interface states their sample size. No confidence interval is calculated.

## Engineering limits

- Single API process and bounded in-process worker pool. Restarted work is marked failed; there is no automatic resume or distributed queue.
- JSON result storage favors auditability over efficient large-scale analytics. Dataset limit: 250,000 events.
- Wallet message authentication and signed-owner observations are implemented. Existing native research CRUD/jobs still lack per-user tenancy and robust quotas; optional API bearer protection remains separate. Use localhost or a trusted access proxy for native research.
- IndexedDB is browser-local. Browser jobs require the tab to stay open; the hosted URL is not a cached offline PWA.
- Floating point arithmetic is suitable for research fixtures, not exact on-chain settlement.

## Next development priorities

1. With provider credentials, ingest and validate a small genuine historical sample, reconcile transactions against an independent explorer, and verify actual plan-specific price/liquidity coverage.
2. Migrate the Helius legacy decoder to current Parsed Events; build a curated corpus of actual transaction fixtures and token-extension rules.
3. Add verified token-creation history, historical universe construction, robust wallet cost basis and token/pool-level execution models.
4. Add a durable native worker queue, research tenancy and atomic admission control before exposing shared native research to unrelated users.
5. Extend the implemented frozen historical audit with prospective observation capture and walk-forward windows with defensible purging/embargo. Any statistical uncertainty method needs its own dependence assumptions and validation.
6. Run Docker Compose/PostgreSQL and a wider responsive/mobile browser matrix in CI.

## This integration's verification boundary

CoinGecko current/history and DEX Screener search returned actual public data. Public RPC wallet reads encountered 429; the tested PublicNode alternative returned 403. No Helius/Birdeye credentials were provided, so real decoded wallet studies, historical price/depth coverage and live detections still require provider access and independent reconciliation. A paid-provider REAL backtest is not represented by the synthetic reference experiment.

The real Phantom adapter is implemented. Tests cover connection approval/rejection/absence, account changes, late responses, message-login/session state and cryptographic server verification. Manual extension approval was not available in this browser. Browser preview access became unavailable during this iteration; new chart rendering and complete extension interaction have not been fully checked there.

Portfolio charts start with actual signed-owner observations, saved at most once per minute. They do not reconstruct past holdings. Missing token prices make these partial valued-subtotal charts. Observations are retained 180 days and queries return the latest 2,000 points; this is not a complete performance/accounting ledger. Hosted research results remain device-scoped IndexedDB.

## Upgrade 1.2.0 audit limitations

- REAL study is blocked by missing Helius/Birdeye server credentials and unverified historical-liquidity entitlement. No independent explorer reconciliation has been completed. See REAL_STUDY.md.
- The included default study remains SYNTHETIC, unchanged seed/configuration. Strategy OOS gross +1.2818%, net -1.9150%; buy-and-hold net +4.2418%; momentum net -8.8826%. Exposure/turnover differ; no alpha claim.
- A fixed historical token/wallet universe can encode future selection and survivorship bias. The lock cannot ensure users have never seen raw data or the unrestricted legacy lab's holdout.
- Hosted experiments persist immutable manifests and lifecycle/result fingerprints in D1. Large detailed outputs and imported datasets remain explicitly device-local. Client computation is not independently certified by the server. Cookie/device loss can lose access to that workspace; export promptly.
- Offline mode uses device-local immutable snapshots through this workflow. Users controlling IndexedDB can alter it; no external timestamp proof exists. Native FastAPI stores full experiment results in SQLite/PostgreSQL.
- Interrupted hosted training/evaluation may remain “running or interrupted” and visible. It is not silently erased or automatically restarted; create another attempt explicitly. Native restart marks interrupted attempts failed.
- REAL bundle redistribution defaults to unconfirmed: observations are omitted unless provenance explicitly says permitted. The authorized original dataset must then be supplied to reproduce. Permission declaration is a user/provider responsibility, not legal clearance by the app.
- Request budgets bound attempts for the initiated study, not account-wide cost/quota or all other users. Cancellation is checked between native provider calls and aborts hosted client requests; an already-running upstream call may finish or consume quota.
- No prospective paper experiment, walk-forward evaluation or on-chain receipt is implemented. Existing live signals are not presented as prospective proof.
- No genuine demand validation, interviews, revenue, partnerships or market-size estimate. Submission scripts are drafts; video recording and manual browser/Phantom/provider interactions require the human team.
