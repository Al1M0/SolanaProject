from contextlib import asynccontextmanager
import secrets
import uuid
from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from .live.providers import LiveError
from .live.routes import router as live_router
from .live.auth import router as auth_router
from sqlalchemy import select, func
from .settings import settings
from .db import SessionLocal
from .models import Dataset, Strategy, Backtest, Trade, Report, Ingestion, Experiment
from .schemas import StrategyInput, BacktestInput, DatasetInput, IngestionInput
from .repository import persist_dataset, load_dataset, dataset_summary
from .demo import generate_demo
from .domain import StrategyConfig
from .jobs import pool, execute_backtest
from .reports import report_markdown
from .ingestion import execute_ingestion
from .providers.readiness import check_readiness
from .experiment_routes import router as experiment_router


def uid(prefix):
    return prefix + "_" + uuid.uuid4().hex[:20]


@asynccontextmanager
async def lifespan(app):
    # Schema is managed by Alembic; startup never silently substitutes create_all.
    with SessionLocal() as db:
        for row in db.scalars(select(Experiment).where(Experiment.status.in_(["training", "evaluating"]))):
            row.status, row.error = "training_failed" if row.status == "training" else "holdout_failed", "Interrupted by restart. Attempt retained; create a new attempt explicitly."
        for row in db.scalars(select(Backtest).where(Backtest.status.in_(["queued", "running"]))):
            row.status, row.error = "failed", "Worker interrupted by server restart; rerun with the saved configuration."
        for row in db.scalars(select(Ingestion).where(Ingestion.status.in_(["queued", "running"]))):
            row.status, row.error = "failed", "Ingestion interrupted by server restart; retry explicitly."
        db.commit()
        if settings.seed_demo and not db.get(Dataset, "synthetic-seed-33"):
            persist_dataset(db, generate_demo())
        if settings.seed_demo and not db.get(Strategy, "strategy-demo"):
            db.add(Strategy(id="strategy-demo", dataset_id="synthetic-seed-33", name="Smart Money Accumulation", config=StrategyConfig().to_dict()))
            db.commit()
    yield


def authorize(request: Request, authorization: str | None = Header(default=None)):
    if request.url.path.startswith(("/api/auth/", "/api/wallets/", "/api/markets/", "/api/live/")):
        return  # Read-only observations; signed-session checks protect wallet writes.
    if settings.api_token and not secrets.compare_digest(authorization or "", "Bearer " + settings.api_token):
        raise HTTPException(401, "A valid API bearer token is required")


app = FastAPI(title="Solana Quant Research Lab", version="1.2.0", lifespan=lifespan, dependencies=[Depends(authorize)], description="Reproducible event-driven research, real mainnet observations and signed-wallet sessions. All datasets explicitly labeled REAL or SYNTHETIC.")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
if "*" in origins:
    raise RuntimeError("CORS_ORIGINS must contain explicit origins for wallet cookie authentication")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT"], allow_headers=["Content-Type", "Authorization"])
app.include_router(live_router)
app.include_router(auth_router)
app.include_router(experiment_router)

@app.exception_handler(LiveError)
async def live_error(request, error):
    return JSONResponse({"detail": str(error)}, status_code=error.status, headers={"Cache-Control": "no-store"})

@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    return JSONResponse({"detail": "Persistent storage is unavailable. Please retry shortly."}, status_code=503)


@app.get("/health")
def health():
    return {"status": "ok", "engine_version": "1.2.0", "execution_mode": "api", "network": "mainnet-beta", "integrations": {"helius": bool(settings.helius_api_key), "birdeye": bool(settings.birdeye_api_key), "mainnet_rpc": True, "coingecko": True, "dexscreener": True}}


@app.get("/api/datasets")
def datasets():
    with SessionLocal() as db:
        return [dataset_summary(r) for r in db.scalars(select(Dataset).order_by(Dataset.created_at.desc()))]


@app.post("/api/datasets", status_code=201)
def create_dataset(body: DatasetInput):
    with SessionLocal() as db:
        try:
            return dataset_summary(persist_dataset(db, body.model_dump()))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc


@app.get("/api/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    with SessionLocal() as db:
        row = db.get(Dataset, dataset_id)
        if not row:
            raise HTTPException(404, "Dataset not found")
        return dataset_summary(row)


@app.get("/api/datasets/{dataset_id}/export")
def export_dataset(dataset_id: str):
    with SessionLocal() as db:
        if not db.get(Dataset, dataset_id):
            raise HTTPException(404, "Dataset not found")
        return load_dataset(db, dataset_id)


def strategy_dict(row):
    return {"id": row.id, "dataset_id": row.dataset_id, "name": row.name, "config": row.config, "created_at": row.created_at}


@app.get("/api/strategies")
def strategies():
    with SessionLocal() as db:
        return [strategy_dict(s) for s in db.scalars(select(Strategy).order_by(Strategy.created_at.desc()))]


@app.post("/api/strategies", status_code=201)
def create_strategy(body: StrategyInput):
    with SessionLocal() as db:
        if not db.get(Dataset, body.dataset_id):
            raise HTTPException(404, "Dataset not found")
        row = Strategy(id=uid("strategy"), dataset_id=body.dataset_id, name=body.config["name"], config=body.config)
        db.add(row)
        db.commit()
        return strategy_dict(row)


@app.put("/api/strategies/{strategy_id}")
def update_strategy(strategy_id: str, body: StrategyInput):
    with SessionLocal() as db:
        row = db.get(Strategy, strategy_id)
        if not row or not db.get(Dataset, body.dataset_id):
            raise HTTPException(404, "Strategy or dataset not found")
        row.dataset_id, row.name, row.config = body.dataset_id, body.config["name"], body.config
        db.commit()
        return strategy_dict(row)


def job_dict(row, detailed=False):
    out = {"id": row.id, "strategy_id": row.strategy_id, "dataset_id": row.dataset_id, "status": row.status, "progress": row.progress, "config": row.config, "error": row.error, "created_at": row.created_at}
    if detailed:
        out["result"] = row.result
    elif row.result:
        out["summary"] = {"dataset_kind": row.result["dataset_kind"], "fingerprint": row.result["fingerprint"], "in_sample": row.result["in_sample"]["metrics"], "out_of_sample": row.result["out_of_sample"]["metrics"]}
    return out


@app.post("/api/backtests", status_code=202)
def start_backtest(body: BacktestInput):
    with SessionLocal() as db:
        strategy = db.get(Strategy, body.strategy_id)
        if not strategy:
            raise HTTPException(404, "Strategy not found")
        dataset = db.get(Dataset, strategy.dataset_id)
        if not dataset.quality["performance_ready"]:
            raise HTTPException(422, {"message": "Dataset is incomplete; performance is blocked", "issues": dataset.quality["issues"]})
        count = db.scalar(select(func.count()).select_from(Backtest).where(Backtest.status.in_(["queued", "running"])))
        if count >= 8:
            raise HTTPException(429, "Worker queue is full; wait for existing research jobs")
        row = Backtest(id=uid("run"), strategy_id=strategy.id, dataset_id=strategy.dataset_id, config=strategy.config, status="queued", progress=0)
        db.add(row)
        db.commit()
        response = job_dict(row)
    pool.submit(execute_backtest, row.id)
    return response


@app.get("/api/backtests")
def backtests():
    with SessionLocal() as db:
        return [job_dict(r) for r in db.scalars(select(Backtest).order_by(Backtest.created_at.desc()).limit(100))]


@app.get("/api/backtests/{run_id}")
def get_backtest(run_id: str):
    with SessionLocal() as db:
        row = db.get(Backtest, run_id)
        if not row:
            raise HTTPException(404, "Backtest not found")
        return job_dict(row, True)


@app.get("/api/backtests/{run_id}/trades")
def trades(run_id: str, segment: str = Query("out_of_sample", pattern="^(in_sample|out_of_sample)$"), offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    with SessionLocal() as db:
        if not db.get(Backtest, run_id):
            raise HTTPException(404, "Backtest not found")
        return [r.payload for r in db.scalars(select(Trade).where(Trade.backtest_id == run_id, Trade.segment == segment).order_by(Trade.id).offset(offset).limit(limit))]


@app.post("/api/backtests/{run_id}/report", response_class=PlainTextResponse)
def report(run_id: str):
    with SessionLocal() as db:
        row = db.get(Backtest, run_id)
        if not row:
            raise HTTPException(404, "Backtest not found")
        if row.status != "completed":
            raise HTTPException(409, "Report requires a completed backtest")
        saved = db.scalar(select(Report).where(Report.backtest_id == run_id))
        if saved:
            return saved.markdown
        text = report_markdown(row.result)
        db.add(Report(id=uid("report"), backtest_id=run_id, markdown=text))
        db.commit()
        return text


@app.post("/api/ingestions/wallets", status_code=202)
def start_ingestion(body: IngestionInput):
    if not settings.helius_api_key:
        raise HTTPException(503, "HELIUS_API_KEY is not configured. No synthetic dataset was substituted.")
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(Ingestion).where(Ingestion.status.in_(["queued", "running"])))
        if count >= 2:
            raise HTTPException(429, "Historical ingestion queue is full")
        job = Ingestion(id=uid("ingest"), request=body.model_dump(), status="queued", progress=0)
        db.add(job)
        db.commit()
        response = {"id": job.id, "status": job.status, "progress": job.progress}
    pool.submit(execute_ingestion, job.id)
    return response


@app.get("/api/ingestions/{ingestion_id}")
def get_ingestion(ingestion_id: str):
    with SessionLocal() as db:
        row = db.get(Ingestion, ingestion_id)
        if not row:
            raise HTTPException(404, "Ingestion job not found")
        # Raw transaction snapshots stay persisted; keep ordinary polling responses small.
        return {"id": row.id, "status": row.status, "progress": row.progress, "error": row.error, "result": {"dataset": row.result["dataset"]} if row.result else None}

@app.post("/api/providers/readiness")
def provider_readiness():
    return check_readiness()

@app.post("/api/ingestions/{ingestion_id}/cancel")
def cancel_ingestion(ingestion_id: str):
    with SessionLocal() as db:
        row = db.get(Ingestion, ingestion_id)
        if not row:
            raise HTTPException(404, "Ingestion job not found")
        if row.status in ("queued", "running"):
            row.status, row.error = "cancelled", "Cancelled by user; no partial dataset published"
            db.commit()
        return {"id": row.id, "status": row.status}
