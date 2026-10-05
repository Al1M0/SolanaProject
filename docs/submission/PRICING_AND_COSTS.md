# Pricing and provider-cost hypotheses

All proposed product prices and unit economics below are **assumptions**, not revenue, validated willingness to pay or a provider quote. No services were purchased.

## Product hypotheses to test

- Free: the synthetic offline audit and reproduction tools.
- Researcher: proposed $19/month for saved review workflows and a bounded number of authorized historical studies.
- Alternative: proposed $5–10 per study, if occasional researchers prefer usage-based access.
- Provider-key option: researchers use authorized server-configured keys; account ownership and data redistribution rights must be explicit. Browser key entry is not implemented.

No checkout, paid tier enforcement or billing integration exists. Interview questions should test the workflow first, then ask how they currently pay for research and which pricing structure would fit.

## Current primary provider facts, checked 2026-10-03

[Helius plans](https://www.helius.dev/docs/billing/plans) describe a Free plan with 1M monthly credits and a Developer plan at $49/month. [Credit documentation](https://www.helius.dev/docs/billing/credits) lists Enhanced Transactions at 100 credits/call in maintenance mode; Parsed Events is a lower-credit successor, not integrated here. The authorized key subsequently retrieved actual address history. The account's remaining quota and commercial unit economics are not verified by that success.

[Birdeye pricing](https://data.birdeye.so/docs/guides/payment/pricing) lists Standard $0/30,000 CU, Lite $39/2.5M CU, Starter $99/8M CU and Premium $199/20M CU. Its [package matrix](https://data.birdeye.so/docs/guides/data-accessibility-by-packages) lists `/defi/history_price` on Standard. The matrix reviewed does not resolve entitlement for the newer historical-liquidity endpoint; obtain an actual access response before selecting a plan.

[Historical prices](https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-history-price) use dynamic CUs (12 up to 100 points; other sizes differ). [1m historical liquidity](https://data.birdeye.so/docs/data-api/price-ohlcv/get-defi-v3-liquidity-history-token) has a 20-CU base with depth/lookback multipliers. These are metering descriptions, not a guaranteed cost for a study.

## Actual access and support update — 2026-10-04

Historical prices worked with the authorized Birdeye key; the required historical-liquidity endpoint returned HTTP 401. The human supplied a Birdeye support reply explicitly confirming that `/defi/v3/liquidity/history/token` is excluded from Standard and requires at least Lite. Support suggested x402 at $0.003/request, but that suggestion does not establish working coverage for this exact endpoint: the prior unpaid discovery/route check did not expose it. No upgrade, x402 payment or service purchase occurred. The prices above are dated public documentation, not a current account invoice or a new purchase recommendation.

The same reply permits normalized observations in a public bundle solely for the research study; commercial use and general data redistribution are excluded. Raw provider-data and Helius rights are not resolved by that reply. Existing export restrictions are retained. See [actual access status and limitations](../REAL_STUDY.md).

## Illustrative small-study assumptions

Assume 3 wallets, 3 days, 1 token, up to 20 Helius pages/wallet: at most 60 logical history calls, roughly 6,000 Helius credits before retries. Roughly 9 small price chunks and 44 liquidity pages imply about 988 base Birdeye CU before dynamic multipliers/retries. Real pagination may be larger, incomplete or empty. Hosted calls reserve two attempts; this example needs approximately 226 attempt slots within the default 240. Request slots do not equal dollars or CUs.

Monthly provider subscriptions may dominate marginal study cost. Proposed pilot envelope: $0–250/month total provider spend, **assumption only**, subject to actual liquidity access, licensing, retries, study volume and account quotas. A $19 subscription may be uneconomic without usage limits or enough customers. Do not claim a gross margin until measured provider invoices and genuine usage exist.
