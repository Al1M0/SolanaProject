# Judge questions and factual answers

**Who is this for?** Independent Solana researchers who manually validate wallet ideas. It is an initial persona hypothesis; no genuine interviews or paying users have been recorded.

**How is this different from Nansen or GMGN?** Those tools document wallet PnL/discovery and smart-money monitoring. This prototype concentrates on a user-defined audit with shared-engine benchmarks, frozen assumptions and a reproducible evidence bundle. We have not verified that competitors lack such a workflow or that users prefer ours.

**Why Solana?** The tested hypothesis uses Solana wallet swaps and token-market observations. Normalization must distinguish wallet economic endpoints from route hops, honor token decimals and preserve signatures for reconciliation. Fees, delay and liquidity matter to this question. No proprietary token or extra chain transaction is required.

**Is the reference dataset real?** No. It is seed-33 SYNTHETIC data used for deterministic engineering validation. Authorized Helius and Birdeye access retrieved actual Solana transactions and historical prices, and five sells matched independent public RPC records. Required price coverage remains incomplete and historical liquidity is denied on the available plan; complete REAL performance is blocked. Public price charts do not substitute for historical execution observations.

**What is the supported coverage?** Small 5-minute studies, at most 14 historical days through ingestion. Hosted backfill allows 5 tokens, native ingestion 20, with request/page limits. Explicit one-input/one-output decoded swaps against SOL/USDC/USDT only. Missing prices/liquidity or incomplete wallet pagination block performance. Scaled-UI unsupported assets and ambiguous routes are excluded.

**How do you prevent look-ahead?** Decisions use prior wallet evidence; entries occur on later bars. Historical prices use a conservative 300-second availability lag. Training/sensitivity exclude later events; segments liquidate separately. Universe selection may still use hindsight, and users may already know raw holdout data. Locking is not proof of an unseen test.

**What does freeze enforce?** SQL persistence prevents manifest/universe/configuration/hash edits. Evaluate requires a frozen snapshot and a one-time lifecycle transition. A change creates a separate attempt. Native results persist in the database. Hosted manifests/lifecycle hashes persist in D1; detailed client-computed results stay on the device. Server storage does not certify client computations. Offline locks are local and can be changed by a user controlling storage.

**Are repeated trials independent?** No. All attempts remain visible. The legacy exploratory lab remains unrestricted and may expose the same historical period; it cannot certify an unseen holdout. No automatic best-trial selection, significance claim or confidence score is provided.

**Are the benchmarks fair?** Same dates, capital, universe, price/liquidity rules, delay and per-side execution costs. Buy-and-hold uses a fixed equal per-token budget capped by the strategy's position budget and 90% of capital divided by token count. Momentum uses a pre-specified +1%/60-minute rule, hourly decisions and 60-minute holds. Eligibility is checked at decision time; failed allocations remain cash. Exposure, turnover and trade counts differ and are reported.

**How exact are costs?** DEX bps, fixed USD network/priority cost, slippage and optional linear liquidity impact are assumptions. The model is not venue-specific AMM replay and does not model MEV, exact on-chain priority costs or fees for submitted failed transactions. Recorded wallet transaction fees are separate observations.

**What did the experiment teach?** The untuned synthetic holdout is +1.2818% gross and -1.9150% net for the hypothesis, +4.2418% net for buy-and-hold, -8.8826% for momentum. Strategy exposure is lower; the result does not demonstrate skill. It demonstrates that costs can erase gross returns and that choosing an easy baseline would mislead.

**How reproducible is it?** Manifest includes dataset SHA-256, provider provenance, controls, split, benchmark rules, seed where used and engine source hash/version. ZIP supplies the standard-library engine, reports, results, trades, exclusions and permitted data. `python3.12 reproduce.py` checks exact fingerprints/results on the verified runtime. Python 3.11 can fail float hashes; no tolerance was added. If redistribution is unconfirmed, data is omitted and the authorized original must be supplied separately.

**What does a hash prove?** Consistency of a particular payload. No accuracy, profitability, absence of bias or unseen holdout. No devnet receipt is implemented. If added later, it would prove only that a hash was recorded by a time, require explicit user action and remain optional.

**Is this prospective paper trading?** No. Live alerts are supporting observations, not a frozen prospective experiment. Prospective capture with gap/interruption accounting and walk-forward with purge/embargo are future work. No trades are submitted.

**Business model?** Proposed $19/month or per-study pricing is unvalidated. Provider entitlement/licensing and usage limits may determine viability. No revenue, partnerships, market-size estimate or measured demand are claimed.

**Remaining weaknesses?** No completed REAL performance study: actual history/prices and five public-RPC swap comparisons are recorded, but historical liquidity is denied and some prices are missing. Human explorer review and manual browser/Phantom approval remain unverified. No genuine user feedback, historical universe bias, aggregate liquidity proxy, small samples, device-local hosted details, in-process native jobs and no production multi-tenant quotas. SQLite/D1 checks pass; Docker/PostgreSQL execution is not verified.
