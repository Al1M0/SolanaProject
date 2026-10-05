# Architecture

The repository is a small monorepo. There is one API and one worker pool, not a fleet of microservices.

```mermaid
flowchart TD
  UI["Next.js research terminal"] --> API["FastAPI / Pydantic"]
  API --> DB["PostgreSQL or SQLite"]
  API --> Worker["Bounded job pool"]
  Worker --> Engine["Portable Python engine"]
  Engine --> Factors["Incremental factor state"]
  Engine --> Rules["Strategy rule registry"]
  Engine --> Metrics["Chronological validation"]
  Worker --> DB
  Providers["Helius / Birdeye adapters"] --> DB
  API --> Providers
  UI --> Browser["Explicit browser research mode"]
  Browser --> WASM["Pyodide Web Worker"]
  WASM --> Engine
  Browser --> IDB["IndexedDB"]
```

## Module boundaries

| Module | Responsibility |
|---|---|
| `backend/app/domain.py` | Validated portable strategy configuration; unsupported fields rejected |
| `providers/` | HTTP retry policy, provider-specific retrieval and normalization |
| `quality.py` | Completeness gates; price/liquidity coverage; duplicate and invalid data checks |
| `factors.py` | FIFO wallet evidence, rolling unique buyers/volume, liquidity, age and momentum |
| `strategies.py` | Allowed strategy registry and `should_enter` rule protocol |
| `engine.py` | Chronological event loop, pending orders, cash, positions, execution and split boundaries |
| `metrics.py` | Returns, drawdown, daily Sharpe, win rate and undefined-metric handling |
| `models.py`, `repository.py` | SQLAlchemy persistence and immutable normalized datasets |
| `jobs.py`, `ingestion.py` | Asynchronous work and persisted job state |
| `reports.py` | Reproducible Markdown report, independent of UI |
| `frontend/lib/api.ts` | Explicit API/browser mode boundary and local persistence |
| `frontend/public/research-worker.js` | Fixed commands into the shared Python code; no arbitrary user code |

## Persistence

- `datasets`: metadata, provenance, quality assessment, content hash and kind.
- `events`: normalized payloads with dataset/event identity uniqueness and a timeline index.
- `strategies`: named research projects, dataset binding and current configuration.
- `backtests`: immutable configuration snapshots, state/progress, errors and complete result JSON.
- `trades`: separately persisted closed trades, indexed by run and segment.
- `reports`: idempotently generated Markdown report per completed run.
- `ingestions`: request, progress, dataset summary and raw provider transaction snapshots.

Alembic migrations `0001`, `0002` and `0003` declare research, wallet auth/observations and immutable experiment schemas explicitly. API startup does not run `create_all`. SQLite uses WAL and foreign keys; PostgreSQL uses psycopg. Datasets cannot be overwritten through the API. Create a new dataset identity when changing observations.

## Execution and deployment

FastAPI returns `202` immediately and the bounded `ThreadPoolExecutor` executes jobs outside the request handler. Ordinary requests continue; a regression test holds a research worker while querying health/datasets. CPU work is still subject to Python's GIL. This is a single-process MVP, not a distributed durable queue. Interrupted jobs are marked failed on restart and can be rerun. Queue limits are best-effort single-host limits, not an adversarial admission-control guarantee.

Docker Compose starts PostgreSQL, the API and Next.js. The private hosted deployment serves static Next.js assets plus an ESM Worker API for real providers and wallet message authentication. D1 persists wallet nonces, hashed sessions, signed-owner observations and immutable audit manifests/lifecycle hashes. Python research runs in WebAssembly; imported REAL datasets and runs persist in browser IndexedDB. PostgreSQL and the native job pool remain native deployment options. The native/WASM parity test checks matching inputs, fingerprints and outputs.

## Extension points

Add a factor to `FACTOR_REGISTRY`, implement its incremental state using only observed events, and extend the typed configuration/API controls. Add a strategy rule to `STRATEGY_REGISTRY` and the allowed `strategy_type` validator; no execution-loop rewrite is required for a new entry rule using the same long-only position lifecycle. Strategies requiring shorting, limit orders or leverage need explicit execution-model extensions.

Implement `HistoricalMarketProvider.fetch` for a new market provider. Its normalized observations must include actual historical timestamps, USD price and historical liquidity, with availability rules and missingness preserved. Never convert transfers to swaps based solely on opposite token movements.

## Real data boundaries

`edge/runtime.ts`, `auth.ts`, `solana.ts`, `market.ts` and `index.ts` provide the hosted read-only service layer and same-origin router. FastAPI equivalents are under `backend/app/live/`. Both validate mainnet, retain null unknowns, bound requests and sanitize errors. Drizzle's committed D1 schema/migration is independent of the native Alembic database.

`normalization.py` and `analytics.py` are portable and shared with the browser worker. They reject transfers/ambiguous economic endpoints, preserve quote units, match FIFO lots conservatively and use strictly prior sales for qualification. `frontend/lib/research.ts` joins actual historical price/liquidity observations into the existing immutable dataset schema. Existing engine quality gates control whether performance may run.

The root `dev` wrapper supports managed preview within the canonical checkout. `scripts/preview-edge.mjs` is a development-only Node/SQLite adapter for the same hosted Worker; it is excluded from the production Worker bundle. Native launch remains unchanged.

## Frozen research audit

`audit.py` selects a fixed universe and invokes the existing execution loop for the hypothesis and two pre-specified policies. `experiments.py` creates content-addressed manifests, training-only sensitivity and a standard-library reproduction ZIP with source checksums. Native `experiment_routes.py` uses the existing thread pool and full SQL experiment persistence. `edge/experiments.ts` persists immutable manifests and lifecycle/result hashes; hosted details remain explicitly device-local, with a separate opt-in offline local lock. Shared scientific computation stays in Python rather than a second TypeScript execution engine.
