# REST API

Native base URL: `http://localhost:8000`. Hosted real-data routes use `/api` on the existing Site origin. Research CRUD/jobs remain FastAPI in native mode and the browser worker/IndexedDB in hosted mode. Interactive schemas: `/docs`; machine-readable schema: `/openapi.json` and the included `docs/openapi.json`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Status, engine version and credential-presence flags; never returns keys |
| GET | `/api/datasets` | Dataset metadata and completeness |
| POST | `/api/datasets` | Import a normalized immutable dataset; schema validation, REAL/SYNTHETIC required |
| GET | `/api/datasets/{id}` | Metadata, provenance and quality |
| GET | `/api/datasets/{id}/export` | Full normalized dataset |
| POST | `/api/ingestions/wallets` | Queue bounded Helius/Birdeye ingestion; returns `202` |
| GET | `/api/ingestions/{id}` | Ingestion status, progress, sanitized error and saved dataset |
| GET | `/api/strategies` | Saved research configurations |
| POST | `/api/strategies` | Create a strategy |
| PUT | `/api/strategies/{id}` | Update current config; previous runs keep their snapshots |
| POST | `/api/backtests` | Queue a strategy run; returns `202` |
| GET | `/api/backtests` | Latest 100 runs with summary metrics |
| GET | `/api/backtests/{id}` | Status/progress and full result once completed |
| GET | `/api/backtests/{id}/trades` | `segment`, `offset`, `limit` (1–500) |
| POST | `/api/backtests/{id}/report` | Idempotent Markdown report for a completed run |

Create and run:

```bash
curl -s http://localhost:8000/api/strategies \
  -H 'Content-Type: application/json' \
  -d '{"dataset_id":"synthetic-seed-33","config":{"min_wallet_count":3,"fee_bps":30}}'

# Substitute the returned strategy id:
curl -s http://localhost:8000/api/backtests \
  -H 'Content-Type: application/json' \
  -d '{"strategy_id":"RETURNED_STRATEGY_ID"}'
```

Poll the returned run ID until `completed` or `failed`. Progress is based on processed event count. Runs can fail honestly; errors do not return invented results.

Request historical ingestion only after configuring server environment keys:

```json
{
  "wallets": ["YOUR_VALID_SOLANA_WALLET_ADDRESS"],
  "start_ts": 1767225600,
  "end_ts": 1767312000,
  "max_pages": 20,
  "include_prices": true
}
```

Times are UTC Unix seconds aligned to five-minute boundaries. Inputs are bounded to 10 wallets, 14 days and 200 wallet-history pages. Ingestion may save an **incomplete REAL** dataset when market access fails. A missing Helius key returns `503` immediately; unsupported coverage never becomes synthetic.

## Normalized events

Market event:

```json
{"id":"source:token:timestamp","type":"market","ts":1767225600,"token":"MINT","price_usd":1.25,"liquidity_usd":200000,"volume_usd":null,"provider":"source"}
```

Swap event:

```json
{"id":"signature:wallet:mint:buy","type":"swap","ts":1767225600,"slot":123,"wallet":"WALLET","token":"MINT","side":"buy","quantity":100,"decimals":6,"execution_price_usd":null,"provider":"helius-enhanced-transactions"}
```

Top-level dataset fields are `id`, `name`, `kind`, `start_ts`, `end_ts`, `resolution_seconds`, `tokens`, `wallets`, `events`, `provenance` and `limitations`. See the bundled synthetic JSON for a complete example. Null unknowns remain null. Dataset identity collisions return `409`.

The existing native research CRUD/job API optionally uses `API_TOKEN`; if configured, pass `Authorization: Bearer TOKEN`. The frontend does not store server/API secrets and does not offer a token-entry flow. Put shared deployments behind a trusted authentication proxy or add research tenancy before exposing the native research API to unrelated users. Docker binds the frontend/API to localhost by default.

## Mainnet and wallet message routes

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/live/status` | Network, provider and credential-presence flags; no key values |
| GET | `/api/markets/sol` | Actual current SOL market observation |
| GET | `/api/markets/search?q=...` | At most 20 distinct Solana base-token markets |
| GET | `/api/markets/{mint}` | Deepest returned base-token pair statistics |
| GET | `/api/markets/{mint}/history?days=7` | Actual provider price history; days 1/7/30 |
| GET | `/api/wallets/{wallet}` | Confirmed SOL and positive standard SPL/Token-2022 holdings, current partial USD valuation |
| GET | `/api/wallets/{wallet}/transactions?before=...` | 20 signatures/page; up to 10 detailed fee/type reads in one batch |
| POST | `/api/auth/nonce` | Same-origin `{wallet}`; five-minute challenge, five requests/minute/wallet |
| POST | `/api/auth/verify` | Same-origin `{id,wallet,signature}`; signature is base64-encoded Ed25519 over the exact challenge message |
| GET | `/api/auth/session` | Current unexpired verified session or null |
| POST | `/api/auth/logout` | Same-origin cookie/session invalidation |
| GET | `/api/wallets/{wallet}/observations` | Signed same-wallet session; saved observations only |
| POST | `/api/wallets/{wallet}/observations` | Signed same-wallet session + origin check; server-derived snapshot, deduplicated per minute |
| GET | `/api/wallets/{wallet}/history?start=...&end=...&before=...` | Helius decoded history, 100/page; only an empty final page establishes complete coverage |
| GET | `/api/markets/{mint}/research-prices?start=...&end=...` | Birdeye, at most 98 five-minute buckets, one-bucket availability lag |
| GET | `/api/markets/{mint}/research-liquidity?time=...` | Birdeye, 100 one-minute historical exit-liquidity observations/page |

History windows are past UTC seconds after 2024-01-01, at most 14 days. Invalid public keys are rejected. RPC genesis must match mainnet-beta. Authentication only signs a message: no transaction RPC or private-key endpoint exists. Saved observations cannot be assigned client-provided price/balance values.

Wallet analytics, accumulation detections and hosted dataset assembly run in the fixed-command Python Web Worker (`analytics`, `accumulation`, `build_real`). They are not hidden HTTP routes or arbitrary user-code evaluation. Insufficient or incomplete data stays labeled as such.

## Hypothesis audit additions

Native API: `POST /api/providers/readiness`, `POST /api/ingestions/{id}/cancel`, `GET/POST /api/experiments`, `GET /api/experiments/{id}`, `POST /api/experiments/{id}/freeze`, `POST /api/experiments/{id}/evaluate`, `GET /api/experiments/{id}/bundle`.

Create body: `{dataset_id, config, token_ids}`. Training executes in the existing bounded worker pool. Freeze/evaluate accept an empty object only; configuration changes require a new experiment. Evaluate is one-time per frozen attempt. Failed attempts remain queryable. New Alembic revision 0003 enforces immutable snapshots.

Hosted API uses the same lifecycle routes with a server-issued HttpOnly anonymous research-workspace cookie, independent of signed wallet sessions. Client-side shared Python produces the manifest/training/holdout; `POST /api/experiments` accepts `{manifest_json, manifest_hash}` and validates its SHA-256. `/training` and `/holdout` accept result fingerprints; `/fail` records interruptions/errors. D1 persists immutable manifests/hash/status/history; large detailed results stay device-local. There is no manifest edit endpoint or server certification of client-generated results. Applied D1 migration 0000 is unchanged; new schema-only migration 0001 adds the audit tables/triggers.
