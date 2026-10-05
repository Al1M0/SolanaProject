# Verification record

## Guided audit, provider errors and export repair — 2026-10-04

Four actual screenshots and one SYNTHETIC audit ZIP supplied by the project builder were opened. They show training, a frozen/evaluated historical holdout, trade evidence and a saved archive. The Markets screenshot shows CoinGecko HTTP 403 for both current prices and history. This proves that those requests were refused; it does not identify the account, entitlement or network cause. The screenshots belong to the preceding release, not a fresh browser run of this change.

The audit now presents one prominent next action derived from the persisted lifecycle, folded setup controls, plain-language cost findings and readable trade timing/cost evidence. Failed/interrupted/evaluated snapshots cannot offer a fresh holdout. Motion reveals actual results without changing plotted values; progress comes from the engine/storage response, and reduced-motion settings disable movement. Invalid portfolios cannot display apparent returns in either cards or the comparison table.

| Check | Actual result |
|---|---|
| Full native `.venv/bin/python -m pytest backend/tests -q` | 103 passed; one upstream Starlette/AnyIO deprecation warning |
| `npm run test:edge` | 21 passed, including bounded actual-source fallback and closed historical observations using fixtures |
| `npm run test:wallet` | 8 passed with injected-provider fixtures; no actual Phantom approval |
| `npm run test:audit-ui` | 10 passed, including persisted next-step states, costs/loss/missing-data findings, invalid metric suppression and HTTP 403 explanations |
| `npm run typecheck` | Frontend and Worker passed |
| Native API frontend production build | Passed with `NEXT_PUBLIC_EXECUTION_MODE=api STATIC_EXPORT=0` |
| `npm run test:wasm` | Native/portable engine parity plus browser JSON roundtrip → ZIP → strict independent native reproduction passed |
| `.venv/bin/python scripts/verify_audit.py` | Actual local HTTP training → freeze → holdout → ZIP → independent reproduction passed with fresh SQLite; SYNTHETIC observations |

**142 automated tests passed.** Production hosted build and source/archive publishing are performed after this record is written; only the native deployment status confirms publication. No fresh manual browser, pointer/timing/mobile inspection or provider interaction from the deployed revision is claimed.

### Export defect found in the builder's actual archive

The original `exp_2d87d7913f2a79fd888713e2` bundle passed file/dataset/manifest integrity, but its exact result-hash check failed. Recursive comparison found **zero unequal result values** and 16,263 float/int representation differences: JavaScript serializes Python `1000.0` as `1000`. A regression check now exercises this boundary rather than testing Python-only exports.

An export adapter reruns the exact frozen snapshot, refuses any changed numeric value, boolean coercion, structure or fingerprint, then packages the original engine with Python's original numeric encoding. It uses no tolerance, selects no parameters, overwrites no attempt and grants no additional holdout lifecycle transition. Dataset, configuration, frozen manifest and engine source remain unchanged.

The corrected separate export of the supplied study passed `python3 reproduce.py` in a fresh directory:

- Dataset SHA-256: `b0e39642e0b97a921fa94f56a6a46e439bdc563a32f6c872a00c73e956482829`.
- Frozen manifest SHA-256: `d23626609f9585adb0af6071793ff971d6d801693af806248cfb5559536b9dd0`.
- Correctly encoded results SHA-256: `55828634a0d74dfbaee86a5daaa789fa78bb5d3f00a2c20d4904179d33018e59`.
- Original engine source remains `source-sha256:697441c3e80d5740405e38f36f16b7b6288b30a269b236d8fe2dfbf9a09d02c5`.

No original screenshot or private uploaded ZIP is added to the source release. The committed seed-33 reference artifact is untouched.

### Provider routing and verification boundary

CoinGecko current-price failure can make one bounded attempt through the existing DEX Screener adapter: only a positive actual wSOL **base-token** pair quote is eligible. The displayed provider, pool and limitations remain visible; it is not relabeled consolidated SOL data. If both sources fail, values remain unavailable. Each upstream uses at most two attempts, with no retry of 401/403. No synthetic provider fallback is introduced.

When a Birdeye key is configured, display-only SOL history now uses the existing Birdeye hourly adapter. Marks become available after bucket close; missing prices stay absent, and no historical liquidity is inferred. Both native/Worker paths are verified with isolated fixtures. Successful requests from the newly deployed version have not been independently verified, and historical-liquidity entitlement/REAL-study coverage remain blocked.

Current primary documentation checked: [CoinGecko HTTP meanings](https://support.coingecko.com/hc/en-us/articles/6472757474457-How-can-I-differentiate-between-the-status-codes-I-am-receiving-and-what-do-they-mean), [DEX Screener API](https://docs.dexscreener.com/api/reference), [Birdeye historical prices](https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-history-price). These documents do not establish the supplied account's entitlement or guarantee production availability.

## Button and motion follow-up — 2026-10-04

CSS-only control styling adds gradients, hover/press feedback, focus rings, selected tabs and brief entrance effects with reduced-motion overrides. `npm run typecheck`, the hosted/offline production build and `git diff --check` passed for this follow-up. No new tests were added; the 129-test record below belongs to the preceding interface release and is not represented as a rerun. Pointer behavior, visual timing and real-browser appearance remain manually unverified.

## Interface release — 2026-10-04

The existing stack and all ten product routes are preserved. The refreshed research desk, grouped navigation, study sheet and audit comparison use existing datasets and results. No engine, provider, seed, benchmark or strategy-default changes were made.

| Check | Verified result |
|---|---|
| Native `.venv/bin/python -m pytest backend/tests -q` | 98 passed; the same upstream deprecation warning |
| `npm run test:edge` | 18 passed |
| `npm run test:wallet` | 8 passed; injected-provider fixtures, not an actual Phantom approval |
| New `npm run test:audit-ui` | 5 passed: timestamp gaps/no fills, invalid portfolios, nonfinite marks, every point in both reference phases, and rendered labels/negative returns/costs/methodology |
| `npm run typecheck` | Frontend and Worker passed |
| Native frontend production build | Passed, all ten product routes |
| `npm run build` | Hosted/offline application and Worker build passed |
| `git diff --check` | Passed |

**129 automated tests passed.** The new React evidence check renders static markup; it is not a manual browser or chart-layout test. Net-equity series join exact engine timestamps with null gaps and no carried/interpolated observations. The reference fingerprints and negative strategy result are retained. Browser/mobile visual inspection and real wallet approval remain unverified for this interface pass; see [the explicit human checklist](UI_REDESIGN.md).

## Release 1.2.0 — 2026-10-03

Verified with Python 3.12 and Node.js 22. Original tests remain; provider fixtures are isolated from application observations.

| Check | Verified result |
|---|---|
| Native suite: `.venv/bin/python -m pytest backend/tests -q` | 98 passed; one upstream Starlette/AnyIO deprecation warning |
| Hosted Worker: `npm run test:edge` | 18 passed with real Ed25519 cryptography and all committed SQLite migrations |
| Phantom state: `npm run test:wallet` | 8 passed using an isolated injected-provider fixture |
| Frontend and Worker TypeScript: `npm run typecheck` | Passed |
| Native API frontend production build | Passed; all 10 product routes, including `/audit` |
| Offline/hosted build: `npm run build` | Passed; self-hosted Pyodide, static frontend and Worker ESM produced |
| Native/WebAssembly: `npm run test:wasm` | Passed; strategy, both benchmarks, training-only sensitivity and actual ZIP generation |
| Fresh native SQLite: `alembic upgrade head` | Passed through revision `0003`; immutable manifest/frozen-hash triggers exercised |
| Hosted SQLite migrations | `0000` and `0001` applied in the Worker suite; immutable manifest/frozen-hash triggers exercised locally |
| Actual native HTTP: `.venv/bin/python scripts/verify_audit.py` | Create/train → freeze → holdout → export → independent subprocess reproduction passed; repeated holdout rejected with 409 |
| Reference ZIP, extracted outside the repository | `python3 reproduce.py` passed with exact manifest and result hashes |
| Headless CLI attempts | Two completed snapshots and one failed holdout retained in a temporary integration check; original output unchanged |
| Source whitespace: `git diff --check` | Passed |

**124 automated tests passed.** Native/WebAssembly comparisons check metrics to absolute tolerance `1e-8`; the complete audit results also match by exact canonical content digest. Bundle reproduction verifies every file checksum, immutable source/dataset/manifest identity and the complete result digest. Numerically equivalent JSON controls are normalized, and canonical Python manifest text survives browser JSON number conversion.

Regression coverage includes benchmark decision chronology, shared execution/cash/cost accounting, allocations that remain cash after failed eligibility, invalid timestamps/prices/depth, observation availability, training/holdout isolation, seven training-only sensitivity rows, immutable SQL snapshots, one-way lifecycle transitions, unsuccessful trial retention, workspace isolation, exports without credentials, redistribution restrictions and deterministic reproduction. Original wallet, backtest, authentication and live-state checks are retained.

## Reproducible SYNTHETIC study

Untuned original seed 33 and default strategy; no selection for profitability. Creation/reproduction dates describe software work, not real market observation dates.

- Experiment: `exp_4514bc9bb0270736afa3555d`
- Dataset SHA-256: `d1472d81d69983de87dad530d89bf0e1f108552086da79719cae74f71d09107d`
- Frozen manifest SHA-256: `cd6d52b8b867e538113b8eef33fd9d67143777ee4af8d8bc15ba4c270536aa6a`
- Full results SHA-256: `2d7ef24b008aa673a49faab584e96996b530fe24277c4f7814ab8865b5757230`
- Engine: `source-sha256:697441c3e80d5740405e38f36f16b7b6288b30a269b236d8fe2dfbf9a09d02c5`

| Phase / portfolio | Gross % | Net % | Costs USD | Trades | Exposure % | Turnover | Failed exclusions |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training — strategy | -4.5303 | -12.7829 | 825.26 | 83 | 7.7877 | 16.4719× | 2 |
| Training — buy-and-hold | -4.2757 | -4.6532 | 37.75 | 4 | 39.1592 | 0.7533× | 0 |
| Training — momentum | +1.0640 | -20.8755 | 2,193.95 | 220 | 11.1212 | 43.7910× | 3 |
| Holdout — strategy | +1.2818 | -1.9150 | 319.68 | 32 | 6.5968 | 6.3808× | 0 |
| Holdout — buy-and-hold | +4.6639 | +4.2418 | 42.21 | 4 | 42.1468 | 0.8426× | 0 |
| Holdout — momentum | +1.4937 | -8.8826 | 1,037.64 | 104 | 11.5245 | 20.7111× | 2 |

Costs erase the strategy's observed positive gross holdout return. Its net result is below buy-and-hold and above this momentum rule in this simulated period. Exposure and turnover differ, so this is not a measurement of skill. Only three complete daily returns occur in the holdout; existing annualized Sharpe values are highly uncertain and are not promoted in the audit comparison. Trades and correlated events are not independent observations. No proven alpha, p-values, confidence intervals or confidence scores are claimed.

Inspect [report](../research/reference/research_report.md), [manifest](../research/reference/manifest.json), [results](../research/reference/results.json) and [reproduction ZIP](../research/reference/reproduction.zip). The actual API integration record is [audit-http-smoke.json](audit-http-smoke.json).

## Actual public provider checks

`scripts/verify_live.py` ran actual local HTTP/provider requests. [live-smoke.json](live-smoke.json) records the check time; these values are not supplied to the UI or promoted to historical research observations.

- Health/live configuration: HTTP 200.
- CoinGecko SOL market and seven-day history: HTTP 200; 169 historical observations.
- DEX Screener JUP search: HTTP 200; three results.
- Official Solana mainnet RPC read: HTTP 429; the application preserved a readable provider failure.

These verify public display endpoints, not an authenticated historical trading dataset.

## REAL-study blocker

The initial keyless readiness check was followed by user-authorized configuration of both production server secrets (environment revision 3). Actual private production API calls verified Helius history and Birdeye `/defi/history_price` access. [provider-readiness.json](provider-readiness.json) now records the remaining `/defi/v3/liquidity/history/token` HTTP 401 permission blocker. The user subsequently supplied Birdeye support's answer: Standard excludes this endpoint and Lite is the minimum subscription. Support permits normalized observations in a public bundle solely for this research study, excluding commercial use and general redistribution. Its suggested x402 alternative is not yet verified for this historical endpoint; no service was purchased. Readiness probes do not certify completeness, quota or redistribution rights.

The fixed 48-hour user-wallet check retrieved 1,519 actual transactions in 17 pages ending with an empty response; 60 supported swaps and 1,459 exclusions were recorded. A token selected by its first chronological supported buy has six swaps, 476 actual historical price marks, 101 missing prices and no historical liquidity over 577 required slots. The unchanged CLI correctly rejected training and retained an immutable failed-attempt manifest/status; it did not freeze or evaluate the holdout. Five deterministic swaps match finalized records from independently queried public Solana RPC, including raw token/quote amounts, direction, time, slot and network fees. All five are sells; manual Explorer/Solscan UI review is still unverified. No plan was purchased. [REAL_STUDY.md](REAL_STUDY.md) links actual quality, provenance, exclusions and reconciliation evidence. Synthetic observations and test fixtures are never renamed REAL.

A later integration check accepted all three human-supplied addresses and exercised the deployed history route for the two new addresses (34 history calls within a 50-call cap). Conservative parsing retained 74 swaps across the combined observed sample. The third wallet's query exhausted after nine pages; the second reached the cap and remains incomplete. The repeated readiness probe still denies historical exit liquidity (401). A new independent account-information request returned 429, so that interaction remains unverified. [The separate checkpoint](../research/three-wallet-access-2026-10-03/research_report.md) records dates, exclusion counts, hashes, limits and remaining blockers. No engine/frontend changes, training or holdout evaluation occurred in this documentation/evidence continuation; the earlier 124-test release is retained, not represented as a newly rerun suite.

## Browser and runtime boundary

The new browser worker's complete audit calculations and ZIP generation were executed in WebAssembly; the new React interaction sequence was **not manually exercised in a supported browser**. Phantom extension approval was not available. Wallet connection/state behavior is fixture-tested, not a recorded real wallet interaction.

The applicable [Sites building SKILL.md](sandbox:/root/.codex/plugins/cache/openai-curated-remote/sites/0.1.75/skills/sites-building/SKILL.md) delegates browser setup to its [managed preview instructions](sandbox:/root/.codex/plugins/cache/openai-curated-remote/sites/0.1.75/skills/sites-building/references/preview/managed-linux.md): “If it is unavailable, do not improvise another browser-control path.” The required `$control-browser` skill is unavailable in this environment; therefore no alternate browser path was used. The same instructions allow validated publication when preview infrastructure is unavailable. Human browser QA remains required before recording the demo.

Hosted D1 schema/lifecycle behavior was tested through local SQLite and Worker handlers. Authorized production readiness/history routes were subsequently exercised over actual HTTP; production D1 experiment interactions and Phantom extension approval remain unverified. Hosted immutable manifests/lifecycle hashes are server-persisted, while imported datasets and detailed computed results stay explicitly on the originating device; the server does not certify client computations. Offline mode has device-only locks, which a user controlling local storage can alter. Native API runs store full results in SQLite; native multi-user research tenancy is not implemented.

Docker/PostgreSQL were not executed. Broad browser/mobile coverage, a distributed job queue, walk-forward purged/embargoed evaluation, prospective paper experiments and devnet receipts remain future work. Customer interviews, recorded videos and the team's actual competition/track eligibility are unverified; the feedback log remains empty.
