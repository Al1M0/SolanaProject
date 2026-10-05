# REAL study status and reconciliation protocol

**REAL performance BLOCKED, checked 2026-10-03 19:48 UTC.** The user supplied Helius/Birdeye keys, configured as server secrets in production environment revision 3. Helius history and Birdeye historical prices are accessible. `/defi/v3/liquidity/history/token` returns HTTP 401: the key lacks sufficient permissions. This is an access blocker, not a missing-key blocker; the user subsequently supplied Birdeye support's 2026-10-04 confirmation that Lite is the minimum subscription and Standard excludes it. No paid plan was purchased.

The user supplied one public wallet from a GMGN 1D-PnL ranking. A fixed 48-hour ingestion check retrieved 1,519 records across 17 pages, with an empty terminal page; the conservative parser retained 60 swaps across 22 tokens and recorded 1,459 exclusions. One token chosen by its first chronological supported buy has six swaps and 476 actual price marks over 577 required slots. Historical liquidity is absent. The engine correctly rejected training and retained its failed attempt; no configuration was frozen and no holdout or REAL returns were evaluated. The historical ranking introduces selection bias. See [report and immutable attempt](../research/real-access-2026-10-03/research_report.md), [quality](../research/real-access-2026-10-03/dataset-quality.json) and [readiness](provider-readiness.json).

Five deterministic swaps matched independently retrieved finalized public RPC records for time, slot, success, raw amounts/decimals/direction, gross WSOL proceeds and network fees. All five are sells. Gross proceeds are not net wallet SOL changes. [Reconciliation evidence](../research/real-access-2026-10-03/reconciliation.json) records actual quantities and source links. Solana Explorer/Solscan pages could not be read with available tools, so manual explorer review remains pending. Raw provider observations remain outside Git/source bundles. The subsequent Birdeye support reply permits normalized observations solely in a public research-study bundle, excluding commercial use/general redistribution; this scoped permission does not settle raw-data or Helius rights. Existing provenance/export restrictions have not been widened.

Exact required access: an authorized Helius key accepted by the Enhanced Transactions address-history endpoint; an authorized Birdeye key accepted by `/defi/history_price` and `/defi/v3/liquidity/history/token` on Solana for the chosen historical window. The account response denied the newer liquidity endpoint; the subsequent support reply confirms Lite is the minimum subscription. The live readiness check probes these endpoints at most six attempts. No paid plan was purchased. Use server environment configuration, never NEXT_PUBLIC_* keys.

## Three supplied addresses — separate intake checkpoint

The human has now supplied all three public profile links. The [bounded three-wallet check](../research/three-wallet-access-2026-10-03/research_report.md) uses the same fixed 48-hour dates and retains the first failed study unchanged. The first and third provider queries end with empty pages; the second reaches its 25-page cap after 2,500 records covering only the latest approximately 17 minutes. Across observed histories, 74 supported swaps and 34 tokens remain after conservative exclusions. No supported token appears for all three in this parsed sample, so it cannot establish the default three-wallet signal. Missing/ambiguous events are not invented and the strategy threshold is unchanged.

The new actual readiness probe at 2026-10-03 20:14 UTC again reports historical exit-liquidity HTTP 401. Independent account classification for the two new addresses is unverified because public RPC returned HTTP 429. The human supplied Birdeye support's subsequent minimum-Lite confirmation, recorded in the status above; no granted access is claimed. Raw provider observations remain outside the source bundle. A provider-query terminal page does not establish complete on-chain or decoder coverage. No three-wallet experiment was frozen and no real returns were computed.

## First genuine study when access is available

1. Choose 1–3 public wallets and a 48–72 hour historical window before reviewing future token returns. Record how wallets/tokens were chosen and why this can still be biased. A short study may be inconclusive.
2. Run provider readiness. Set an explicit request budget and page limits. Import actual decoded history and both historical observation series. Save coverage, exclusion counts, parser version, retrieval times, continuation cursors, lag rules and the resulting content hash.
3. Review quality. Missing required prices/liquidity, incomplete transaction pagination, conflicting records or unknown required token ages block performance. Do not interpolate missing history or use current prices/depth to complete it.
4. Select a deterministic reconciliation sample: first five supported swaps ordered by `(timestamp, signature, wallet, token)`; also first supported native-SOL quote swap if it is not already in the sample. No profitable-only sampling.
5. Independently open each signature in [Solana Explorer](https://explorer.solana.com/) or [Solscan](https://solscan.io/). Check finalized success, slot/block time, wallet-owned input/output mints, raw token amounts/decimals, economic direction, route hops and network fee. Record explorer URL, observed values, differences, reviewer and time. A supplied provider response or unit-test fixture is not an independent reconciliation.
6. Treat any mismatch as unresolved. Exclude/reparse with a documented reason and create a new immutable dataset rather than changing the existing experiment. Run the audit even if returns are negative. Record sample limits and provider/explorer discrepancies.
7. Confirm redistribution rights. Default REAL bundles exclude provider observations when permission is unknown; supply the exact authorized dataset locally for reproduction.

## Manual explorer review log — pending

| Signature | Explorer URL | Provider slot/time | Explorer slot/time | Wallet legs/raw amounts/decimals | Direction | Observed fee | Difference/action | Reviewer/time |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

Rows above are slots for future human explorer reviews, not completed manual reviews. The separate public-RPC comparison is recorded in the linked reconciliation artifact. The seed-33 reference study and all parser/provider test fixtures remain engineering simulations and are never promoted to REAL evidence.
