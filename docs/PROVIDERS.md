# Provider verification

Reviewed against official documentation on **2026-10-03**. The earlier keyless check used isolated fixtures; subsequently the user supplied authorized server keys. Production history/prices now have actual successful checks, while historical liquidity is denied to the key. Fixture tests, genuine observations and the synthetic demo remain separate. See [actual access evidence](../research/real-access-2026-10-03/verification.json).

## Helius

Official references:

- https://www.helius.dev/docs/enhanced-transactions/transaction-history
- https://www.helius.dev/docs/api-reference/enhanced-transactions/gettransactionsbyaddress
- https://www.helius.dev/docs/enhanced-transactions/overview
- Official `helius-sdk` npm package, repository `https://github.com/helius-labs/helius-sdk`; legacy `1.5.2` `SwapEvent` / `TokenBalanceChange` types checked for event structure, and current `3.2.0` checked for history API types.

Implemented request: `GET https://mainnet.helius-rpc.com/v0/addresses/{wallet}/transactions`, with `api-key`, `gte-time`, `lte-time`, `before-signature`, `sort-order=desc`, `limit=100`, `token-accounts=balanceChanged` and `commitment=finalized`.

The current documentation marks Enhanced Transactions as legacy/maintenance mode and recommends the newer transaction/Parsed Events products for new integrations. The still-supported legacy endpoint is used here for a narrow explicit-swap MVP. Migration is a documented next step, not a claimed implemented feature.

All transaction types are retrieved; only explicit `type=SWAP` with unambiguous top-level `events.swap` economic legs for the selected wallet is parsed. We do not infer swaps from transfers or count inner route hops. Native amounts use 9 decimals; SPL amounts use supplied raw decimals. SOL/USDC/USDT quote values remain quote values, without assumed USD conversion. Unsupported records are counted. History is considered complete only when pagination reaches an empty response, not simply a short page.

## Birdeye

Official references:

- https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-history-price
- https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-v3-liquidity-history-token
- https://data.birdeye.so/docs/data-api/price-ohlcv

Price: `GET /defi/history_price`, using `address_type=token`, `type=5m`, `time_from`, `time_to` and `ui_amount_mode=raw`. The documented response has `data.items[].unixTime` and `value`. The adapter uses bounded chunks and checks gaps rather than assuming complete provider coverage. Scaled-UI tokens are rejected.

Liquidity: `GET /defi/v3/liquidity/history/token`, using `resolution=1m`, `time`, `direction=back`, `count=100`. Documentation lists historical support from 2024-01-01, with 1m/4h/1D snapshots. The adapter reads `unix_time` and `exit_liquidity_usd`, preserving total `liquidity_usd` separately. It pages backward, samples exact five-minute timestamps, and leaves missing values null.

Both use `X-API-KEY` and `x-chain=solana`. Actual entitlement, supported tokens, retention and missingness still require checking returned observations with the user's plan. Documentation support is not proof of successful retrieval.

Native and hosted research routes validate every observation's timestamp against the requested window and provider resolution. Missing/non-finite numeric values remain null, while negative depth, non-positive prices and malformed timestamps reject the response with HTTP 502 before import. Tests exercise both server implementations using explicit fixtures.

## Availability assumptions

Price line-series bucket timing is not treated as an instantaneous executable quote. Each point is available to this research model one five-minute bucket later; its original timestamp is retained. Liquidity snapshot values represent historical candle-open observations. No current endpoint, price interpolation or missing-liquidity substitute is used. These are conservative coarse observations, not full exchange/AMM replay.

Provider errors are sanitized to avoid API keys embedded in URLs. Rate-limit and transient-server failures retry at most five times with bounded delays. Network access is never attempted in synthetic demo mode.

## Phantom, RPC and display market providers

- Phantom injected `window.phantom.solana`: connect/disconnect, accountChanged/disconnect events, and UTF-8 `signMessage`. References: https://docs.phantom.com/solana/establishing-a-connection and https://docs.phantom.com/solana/signing-a-message . The production app has no provider mock or private-key handling.
- Solana JSON-RPC: `getGenesisHash`, `getBalance`, `getTokenAccountsByOwner` for standard SPL and Token-2022, `getSignaturesForAddress`, and `getTransaction`. Only read methods are used; unordered batch replies are matched by ID. Reference: https://solana.com/docs/rpc/http . Public RPC rate/access limits can block data; a configured mainnet endpoint overrides the default.
- CoinGecko: `/coins/markets?vs_currency=usd&ids=solana` and `/coins/solana/market_chart`, preserving actual timestamps. Reference: https://docs.coingecko.com/reference/coins-id-market-chart . No executable historical liquidity is inferred from these charts.
- DEX Screener: Solana token quotes batched by 30 mints, at most 60/wallet snapshot; search is capped at 20 distinct mints. Only pairs where the requested mint is the base token can supply its USD price. Reference: https://docs.dexscreener.com/api/reference . Current deepest-pair liquidity is a current market observation, not historical depth.
- GeckoTerminal public API: base-token pool discovery and closed hourly USD OHLCV when Birdeye is absent. Empty intervals are omitted, exact returned times retained, no current reserves inserted into backtests. Provider access/rate limits still apply. Reference: https://docs.coingecko.com/reference/pool-ohlcv-contract-address . The public compatibility API used is `https://api.geckoterminal.com/api/v2`.

Public HTTP checks are recorded in `docs/live-smoke.json`. No successful paid-provider backfill is claimed without keys and plan-specific verification.

## Access recheck 2026-10-03

`POST /api/providers/readiness` distinguishes missing keys, rejected access and accessible endpoint response. It uses at most six HTTP attempts. Key presence alone is not entitlement. Production environment revision 3 has both server secrets: Helius history and Birdeye historical prices respond successfully; historical exit liquidity returns HTTP 401 with insufficient permissions. Local dotenv files were not populated with credentials. The fixed 48-hour user-wallet ingestion and independent public RPC comparison are recorded in [REAL access research artifacts](../research/real-access-2026-10-03/research_report.md); missing liquidity/prices correctly block performance. Manual explorer review remains pending.

Primary references: [Helius plans](https://www.helius.dev/docs/billing/plans), [Helius credits](https://www.helius.dev/docs/billing/credits), [Birdeye package matrix](https://data.birdeye.so/docs/guides/data-accessibility-by-packages), [Birdeye pricing](https://data.birdeye.so/docs/guides/payment/pricing), [historical price](https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-history-price), [historical liquidity](https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-v3-liquidity-history-token). History-price is listed on Standard. On 2026-10-04 the user supplied Birdeye support's explicit confirmation that `/defi/v3/liquidity/history/token` is excluded from Standard and requires at least Lite. The current production key still returns 401. Support suggested x402 access, but a working historical-liquidity route remains unverified; no service was purchased. Its normalized-data permission is restricted to public bundles used solely for this research study, excluding commercial use and general redistribution. This does not establish permission for raw data or another provider.

Native full ingestion default budget is 240 actual HTTP attempts, including retries (user maximum 1,500); errors are sanitized and native cancellation persists. Hosted small-study budget reserves the maximum two attempts per proxy call, conservatively bounding upstream retries; the UI shows the upper bound and supports AbortController cancellation. It does not measure provider dollars/CUs. The server never sends keys to the browser.
