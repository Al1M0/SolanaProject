# Three-wallet REAL access and coverage check

**REAL performance BLOCKED. No strategy, benchmark, training or holdout return was computed in this intake attempt.** Checked 2026-10-03T20:15:10.041934+00:00.

The human supplied three public GMGN address-profile links. All decode to distinct 32-byte Base58 addresses and each returned actual Helius history. This verifies address format and available provider observations, not ownership, profitability or a smart-money label. The independent finalized `getAccountInfo` probe returned HTTP 429; no account classification is claimed. See [account check](account-check.json).

This is a separate intake record. It preserves the first failed real study and reuses that study's first-wallet history with a recorded content hash. The second and third histories were requested only after [selection and limits](selection.json) were recorded. All use the same fixed dates: **2026-10-01 19:00 UTC through 2026-10-03 19:00 UTC** (Oct 2 00:00 through Oct 4 00:00, Asia/Almaty). No dates or strategy thresholds were changed to obtain profits.

| Wallet | Provider records | Unique wallet/signature identities | Pages | Query exhausted | Supported swaps | Buys / sells | Tokens |
|---|---:|---:|---:|---|---:|---:|---:|
| 1: `8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6` | 1,519 | 1,519 | 17 | Yes, empty terminal page | 60 | 22 / 38 | 22 |
| 2: `BQVz7fQ1WsQmSTMY3umdPEPPTm1sdcBcX9sP7o6kPRmB` | 2,500 | 2,491 | 25 | No, 25-page cap reached | 0 | 0 / 0 | 0 |
| 3: `215nhcAHjQQGgwpQSJQ7zR26etbjjtVdW74NLzwEgQjP` | 763 | 763 | 9 | Yes, empty terminal page | 14 | 7 / 7 | 12 |

The second wallet's 2,500 returned records cover **2026-10-03 18:43:06–19:00:00 UTC**, only the latest approximately 17 minutes of the requested 48 hours. The pre-specified 25-page cap prevented an unbounded download. Its nine repeated signatures are excluded; no supported unambiguous swap was retained. History remains incomplete with a continuation cursor in the private working data. This is an ingestion limitation, not evidence that the wallet does not trade. No additional pagination is silently represented as complete.

Across the observed histories, the existing conservative parser retains **74 swaps across 34 tokens**, from **4,773 wallet/signature identities**. It records 4,141 non-supported types, 491 missing explicit swap events, 65 ambiguous wallet-leg cases, two unsupported quote pairs and nine duplicate/missing-signature exclusions. Transfers, unknown routes and inner route hops are never treated as wallet accumulation. Per-wallet exclusions, coverage and history SHA-256 hashes are in [ingestion-summary.json](ingestion-summary.json).

**No supported token appears for all three wallets in this parsed sample.** The default three-wallet accumulation signal cannot be established from these observations. Incomplete pagination and decoder exclusions mean this does not demonstrate that no joint activity occurred. The threshold was not lowered and another wallet was not selected to manufacture a favorable result.

## Remaining access and quality blockers

The [actual readiness check](readiness.json) at 20:14 UTC confirms that Helius decoded history and Birdeye historical five-minute prices respond. Birdeye historical exit liquidity still returns **HTTP 401**. The key's exact granting package and any temporary student access remain unconfirmed. The human reports sending a support request; no response or permission grant is yet recorded. No paid service was purchased.

Before any real performance, complete required transaction coverage, historical prices, historical exit liquidity and decision-time token eligibility for a pre-specified token universe. The earlier single-token attempt already documents missing prices and no liquidity; this intake does not repair it or rename it as ready. Manual explorer review of the independent first-wallet RPC comparison remains pending. No independent swap reconciliation is claimed for the two new wallets.

Selection bias remains visible: the first wallet came from a 1D-PnL ranking overlapping the historical period; the exact ranking and filters for the two later user-supplied addresses are not independently verified. This historical universe is not guaranteed unseen. A future study may remain negative or inconclusive.

## Request and redistribution boundaries

The two new histories used **34 private Site history calls** against a pre-specified cap of 50, plus one readiness call. With at most two provider attempts per history call and six readiness attempts, the conservative upper bound is **74 upstream attempts**; actual upstream attempts and credit charges are not observable from these hosted responses and are not claimed. First-wallet history was reused from its earlier query. No market-history series was additionally requested for these new addresses.

Raw responses, normalized trades and continuation cursors remain outside Git and the shareable source ZIP pending provider redistribution permission. This folder includes only selection, non-secret access/coverage metadata, hashes and this report. It is a research-access checkpoint, **not an experiment reproducibility bundle or a frozen three-wallet backtest**. The app, execution engine and untuned SYNTHETIC reference results are unchanged.
