# Local setup and technical operating guide

Commands are run from the repository root unless a step changes directory. This guide preserves the existing application and launch paths.


Audit a wallet-based Solana hypothesis against buy-and-hold and pre-specified momentum after modeled costs. Inspect training, freeze the configuration, evaluate a separate historical period and export a reproducible research bundle. The existing Next.js/FastAPI stack, portable Python engine, offline demo and wallet/market supporting pages are preserved.

**REAL performance currently blocked:** authorized server keys now retrieve actual wallet history and historical prices. The first fixed 48-hour check has 1,519 transactions and 60 supported swaps; five swaps match independent public RPC records. Historical liquidity is denied to the supplied key, some prices are missing, and human explorer review remains pending. All three user-supplied addresses are now recorded; a [separate bounded ingestion check](../research/three-wallet-access-2026-10-03/research_report.md) retains 74 swaps, with incomplete second-wallet history and no supported token shared by all three in this parsed sample. See [REAL study status](REAL_STUDY.md). The untuned seed-33 study remains SYNTHETIC and is not profitable for the wallet strategy after costs.

**REAL and SYNTHETIC are explicit labels.** The included seed-33 study is simulated. Provider failures never substitute simulated balances, prices, transactions or signals.

## Open the deployed app

Use the existing Site; public viewing was enabled on 2026-10-05. Its frontend calls `/api` on the same HTTPS origin; the deployed Worker fetches providers and stores signed wallet sessions/observations in D1. Audit manifests, frozen hashes and lifecycle records persist in D1; detailed client-computed results and imported datasets remain explicitly device-local. The server does not certify client computations. An explicit offline audit mode stores its lock on this device only. The same Python modules run in a self-hosted Pyodide worker.

- **Audit this hypothesis:** dataset/quality → training versus both benchmarks → seven pre-specified training-only sensitivity rows → Freeze → one historical holdout → trade/cost evidence → reproduction ZIP. Each trial is preserved; edits create a new attempt. A historical holdout is not guaranteed unseen.
- **Connect Wallet → Phantom → Approve:** shows the returned public address. Disconnect and Phantom account changes clear stale data and local session state.
- **Wallet → Sign in with Phantom:** requests a five-minute nonce, signs a readable message and verifies Ed25519 on the server. Login never creates or signs a transaction. Sessions expire after 24 hours; cookies are HttpOnly, Secure on HTTPS and SameSite=Lax. Nonces are consumed atomically, including invalid signature attempts.
- **Wallet:** confirmed SOL/SPL/Token-2022 balances, exact decimal amount strings, partial USD valuation, bounded recent transactions, fees and explorer links. A watch-only public address does not require login. Scaled-UI/interest-bearing tokens are displayed without unsupported USD valuation.
- **Markets:** SOL price/change/volume/cap, Solana token search, mint selection and 1/7/30-day provider history. Unknown fields show N/A. Chart gaps remain gaps.
- **Wallet research:** retrieve decoded Helius history, inspect observed trades and conservative quote-denominated FIFO evidence, export it, and import a REAL dataset into the audit workflow. Provider readiness, explicit attempt budget, progress and cancellation are available. Price/liquidity backfill requires Birdeye. Missing coverage blocks performance.
- **Live signals:** user-started, visible-page polling of selected wallets; strictly prior matched-sale evidence and unique buyers. No automatic trading. The initial history is bounded; later polls fetch overlapping incremental updates and periodically resync.
- **Backtests:** delayed modeled entries/exits, gross/net returns, average/median returns, drawdown, win rate, profit factor and sample-qualified Sharpe; network/DEX/slippage/liquidity-impact assumptions are separate and inspectable.

## Server settings

Provider keys stay server-side. Never put them in `NEXT_PUBLIC_*`.

| Setting | Purpose |
|---|---|
| `SOLANA_RPC_URL` | Optional read-only mainnet RPC. Empty uses Helius when configured, otherwise the official public RPC. Genesis is verified. A dedicated endpoint is advisable for reliable balances/history. |
| `HELIUS_API_KEY` | Mainnet RPC and decoded historical swaps/near-live monitoring. |
| `BIRDEYE_API_KEY` | Historical token USD marks and historical exit liquidity for research. Plan access and coverage still matter. |
| `COINGECKO_DEMO_API_KEY` | Optional CoinGecko Demo access; public requests are attempted when absent. |
| `APP_ORIGIN` | Exact frontend origin for message domain/URI and same-origin write validation. Set to the deployed HTTPS origin. |
| `CORS_ORIGINS` | Native FastAPI only: explicit frontend origins, never `*` with wallet cookies. |
| `SESSION_COOKIE_SECURE` | Native FastAPI: `true` in HTTPS production; local defaults are `false`. |
| `DATABASE_URL` | Native research/auth persistence: SQLite or PostgreSQL. |

Hosted builds explicitly use `NEXT_PUBLIC_EXECUTION_MODE=browser` and empty `NEXT_PUBLIC_CHAIN_API_URL`/`NEXT_PUBLIC_API_URL`. Runtime provider settings belong to the server. The deployed private access boundary is retained. Wallet login isolates saved observations; it does not introduce multi-user tenancy into the existing native research API.

## Local native stack

Python 3.12+, Node.js 22+, npm. From the root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example backend/.env
cd backend
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

In a second terminal:

```bash
npm --prefix frontend ci
npm --prefix frontend run prepare:browser
NEXT_PUBLIC_EXECUTION_MODE=api NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_CHAIN_API_URL=http://localhost:8000 npm --prefix frontend run dev
```

Open `http://localhost:3000`. API schemas are at `http://localhost:8000/docs`. SQLite persists at `backend/quantlab.db`. Migrations include research, wallet auth/observations and immutable experiments through revision 0003. Use one API process; the original job pool is single-process.

## Fast offline research demo

The downloadable ZIP includes the built browser application and its local Python runtime. No Node packages, provider keys or Python packages are required for this path. From the extracted project root:

```bash
python3 -m http.server 3000 --bind 127.0.0.1 --directory frontend/out
```

Open `http://localhost:3000/audit/`, enable **Offline audit**, then inspect training, freeze and evaluate the holdout. The local lock is not an independent timestamp or server certification. The legacy Strategy lab remains available. The strategy, trades, costs and validation are computed by the Python engine. Every demo dataset is **SYNTHETIC**. The wallet, market and live pages require a running API and will show unavailable states on this plain static server. For those features use the native stack above or the deployed app.

Docker remains available:

```bash
cp .env.example .env
docker compose up --build
```

Compose publishes localhost frontend/API ports and uses PostgreSQL. Docker/PostgreSQL have not been executed in this environment; SQLite and native/API builds have been verified.

## Build and verify

```bash
npm ci
npm --prefix frontend ci
npm run typecheck
npm run test:edge
npm run test:wallet
npm run test:audit-ui
npm run test:wasm
cd backend
../.venv/bin/python -m pytest -q
cd ..
npm run build
python3 scripts/run_audit.py --output research/reference
```

The hosted build emits `dist/client` and the Worker at `dist/server/index.js`. Committed Drizzle migrations are packaged for D1 by the hosting workflow. Provider mocks are confined to tests.

Create a source ZIP with the built offline demo after `npm run build`:

```bash
python3 scripts/package_release.py --output ../solana-quant-research-lab.zip
```

The release excludes installed dependencies, local databases, private environment files and preview state.

For an optional real HTTP/provider check:

```bash
.venv/bin/python scripts/verify_live.py
```

This starts and terminates its own local FastAPI process, checks actual upstream APIs and writes a timestamped verification record. It does not feed its results into the UI.

A plain static server can run the synthetic browser research demo from `frontend/out` after a build, but cannot serve real-data/auth API routes. Use the full native stack or the deployed Worker for those features.

## Current verification and limits

Actual CoinGecko current/history and DEX Screener search responses were received. The official public RPC returned HTTP 429 during wallet checks; a tested alternative returned HTTP 403. These errors remain visible. Authorized Helius/Birdeye server keys subsequently retrieved actual history and prices; historical exit liquidity remains denied and required price coverage is incomplete, so REAL performance is blocked. No wallet extension was available for manual Phantom Approve; connection/state tests use an isolated provider mock and backend signature tests use real cryptography.

See [verification](VERIFICATION.md), [API](API.md), [providers](PROVIDERS.md), [architecture](ARCHITECTURE.md), [methodology](METHODOLOGY.md), and [limits](LIMITATIONS.md).

## Interface refresh — 2026-10-04

The research desk now leads with one hypothesis and its actual dataset quality. Research navigation is grouped apart from supporting on-chain tools. Audit stages follow the experiment lifecycle, and a study sheet shows the selected universe, execution assumptions and chronological split. Training/holdout views compare exact net-equity curves from the shared engine, with gross/net returns, costs, findings, activity and trade evidence retained. Missing observations stay gaps; no engine defaults or reference results were tuned. See [design rationale and browser checklist](UI_REDESIGN.md) and [verification](VERIFICATION.md).

## Reference research and submission kit

The existing configuration/seed is retained, without profitability tuning. SYNTHETIC holdout: strategy +1.2818% gross / -1.9150% net, buy-and-hold +4.2418% net, momentum -8.8826% net. Exposure/turnover differ; no proven alpha. Inspect [the report](../research/reference/research_report.md) and [summary](../research/reference/summary.json).

Unzip `research/reference/reproduction.zip`, then run:

```bash
python3 reproduce.py
```

Standard-library Python 3.10+ is sufficient. The ZIP includes manifest, configuration, dataset where permitted, exact engine source, trades, results, exclusions and report. REAL observations with unconfirmed redistribution rights are omitted; supply `--dataset /authorized/original.json`. Export blocks credential-like fields.

The headless `scripts/run_audit.py` also preserves attempts: if its output already contains a manifest, the new trial goes under `attempts/<experiment-id>/` and the command prints the actual bundle path. Failed training/holdout attempts retain their manifest and status. Existing snapshots are not overwritten.

[Submission materials](submission/) include positioning, current primary-source competitor comparison, pricing/provider-cost assumptions, five-user interview/usability guide, empty feedback log, English pitch/demo scripts, judging Q&A, rules and factual development-history disclosure. Video files and customer evidence have not been created.

Highest-value human tasks: obtain authorized historical-liquidity access and reconcile a small genuine study; manually exercise browser/Phantom and export; recruit five researchers; confirm the registered competition and record the timed videos. Optional prospective paper experiments and devnet receipts remain future work.
