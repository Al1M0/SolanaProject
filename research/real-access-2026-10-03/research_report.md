# REAL ingestion check — performance blocked

A user supplied one public Solana wallet, `8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6`, from the GMGN list sorted by 1D PnL. The fixed window is **2026-10-01 19:00 to 2026-10-03 19:00 UTC** (2026-10-02 00:00 to 2026-10-04 00:00 Asia/Almaty). Selection was recorded before fetching history. Ranking selection overlaps this historical period: this sample has hindsight selection bias and does not establish an unseen holdout or smart-money skill.

## Genuine observations and exclusions

Production Helius access returned 1,519 unique transaction records across 17 pages, ending in an empty response. The original 10-page attempt (1,000 records, incomplete) was retained locally; a separate continuation attempt completed the same dates and cursor, with no change after viewing returns. Parser outputs: 60 supported swaps over 22 tokens; 1,030 other transaction types, 45 ambiguous wallet-leg swaps and 384 SWAP-labelled records without the required explicit event were excluded. These are actual provider records, not fixtures. Coverage means the endpoint pagination completed for this selected period; it does not prove decoder coverage or completeness of every on-chain activity.

For a bounded price check, choose the token in the first chronologically observed supported buy, using timestamp/slot/event ID, before fetching its price series. Mint: `GAwhcphCqCv5bKHmCiN4VDdNWfbXJL4npmkc8L3Q9S9H`. This selection uses no future price returns. Its six supported swaps were retained; other tokens are an explicit universe exclusion. The token itself is not presumed profitable or to have existed throughout the whole period.

Birdeye returned 476 actual historical five-minute USD price marks across six requests. Marks become available 300 seconds after the provider timestamp. The fixed grid has 577 slots: 101 prices are absent (82.4957% price coverage). No interpolation or current-price substitute was made. The historical exit-liquidity endpoint rejects this authorized key with HTTP 401 and reports insufficient permissions. Historical liquidity coverage is 0%; missing depth remains null. The exact package granting this newer endpoint has not been confirmed from official plan documentation. No purchase was made.

## Independent reconciliation

Five swaps were selected by the documented rule: first five supported swaps sorted by `(timestamp, signature, wallet, token)`. The first native-SOL quote is already included. All five happen to be sells, so this check does not validate buys. Independently fetched public Solana mainnet JSON-RPC records (`getTransaction`, finalized, jsonParsed) match success, slot, block time, owner-token raw amount/direction, decimals, gross WSOL output and network fee in all five records. Temporary WSOL ownership was checked through account initialization; route hops are not counted as separate wallet trades.

Gross WSOL proceeds differ from net wallet SOL changes because platform transfers/tips, network fees and rent can intervene. The raw gross output is not net wallet PnL. See [reconciliation.json](reconciliation.json) for quantities, differences, links and scope. Solana Explorer/Solscan pages could not be read by the available web tool, so **human explorer UI review remains pending**. Independent RPC reconciliation must not be described as completed manual explorer review.

## Audit attempt and what it teaches

The original default strategy was used unchanged. The current one-wallet universe also cannot satisfy its three-wallet accumulation threshold; no lower threshold was selected to produce trades. Training correctly stopped on missing historical prices and liquidity. The failed attempt is retained in [manifest.json](manifest.json) and [status.json](status.json). No configuration was frozen, no holdout was evaluated, no returns/benchmarks were calculated, and no REAL reproducibility-performance bundle is claimed. The complete offline SYNTHETIC reference remains unchanged and usable.

The user learns that a wallet ranking and available transaction history are insufficient to audit a net trading hypothesis. Decoder exclusions, period coverage, lagged historical prices and permissioned liquidity must be visible before any performance claim.

## Reproduction and access

Dataset SHA-256: `7f5ed1b4408049bd35885fc22a0fa2e471c978ca9ba6cfa7dfdf34edc8931e94`.

Keep the authorized immutable dataset locally and run:

```sh
.venv/bin/python scripts/run_audit.py --dataset /absolute/path/to/authorized/dataset.json --manifest research/real-access-2026-10-03/manifest.json --output /absolute/path/to/new/attempt
```

The expected result is the same `Performance blocked` training error and a retained failed-attempt status, not performance results. Full provider observations remain outside Git/source ZIPs because redistribution permission is unconfirmed; there is no dataset in this folder and no API keys or session credentials. The live provider API must be reauthorized to collect a new dataset; a new retrieval is a new snapshot and may have a different fingerprint.

Before a REAL performance demo: obtain provider-confirmed access to `/defi/v3/liquidity/history/token` for the chosen Solana window without an assumed paid upgrade; obtain the genuinely missing prices or document decision-time token eligibility in a new experiment; select enough wallets under a recorded protocol; and finish the linked human explorer review. Do not adjust dates, universe or thresholds until the demonstration becomes profitable.
