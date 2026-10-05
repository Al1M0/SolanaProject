from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, update, func
from .db import SessionLocal
from .models import Dataset, Experiment
from .schemas import StrategyInput
from pydantic import Field, BaseModel, ConfigDict
from .engine import digest
from .repository import load_dataset
from .experiments import create_manifest, train_experiment, evaluate_experiment, now
from .export_validation import verified_bundle_zip
from .jobs import pool

router = APIRouter()
class EmptyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ExperimentInput(StrategyInput):
    token_ids: list[str] = Field(min_length=1, max_length=100)

def row_dict(row):
    return {"id": row.id, "dataset_id": row.dataset_id, "manifest": row.manifest, "manifest_hash": row.manifest_hash, "status": row.status, "frozen_hash": row.frozen_hash, "training": row.training, "sensitivity": row.sensitivity, "holdout": row.holdout, "error": row.error, "history": row.history, "created_at": row.created_at}

def transition(row, state):
    row.status = state
    row.history = [*row.history, {"state": state, "at": now()}]

def execute(id, phase):
    try:
        with SessionLocal() as db:
            row = db.get(Experiment, id)
            manifest, frozen_hash = row.manifest, row.frozen_hash
            dataset = load_dataset(db, row.dataset_id)
        result = train_experiment(dataset, manifest) if phase == "training" else evaluate_experiment(dataset, manifest, frozen_hash)
        with SessionLocal() as db:
            row = db.get(Experiment, id)
            if phase == "training":
                row.training, row.sensitivity = result["training"], result["sensitivity"]
                transition(row, "trained")
            else:
                row.holdout = result
                transition(row, "evaluated")
            row.error = None
            db.commit()
    except Exception as error:
        with SessionLocal() as db:
            row = db.get(Experiment, id)
            transition(row, "training_failed" if phase == "training" else "holdout_failed")
            row.error = str(error)
            db.commit()

@router.get("/api/experiments")
def list_experiments():
    with SessionLocal() as db:
        return [row_dict(row) for row in db.scalars(select(Experiment).order_by(Experiment.created_at.desc()))]

@router.post("/api/experiments", status_code=202)
def create(body: ExperimentInput):
    with SessionLocal() as db:
        if not db.get(Dataset, body.dataset_id):
            raise HTTPException(404, "Dataset not found")
        if db.scalar(select(func.count()).select_from(Experiment).where(Experiment.status.in_(["training", "evaluating"]))) >= 8:
            raise HTTPException(429, "Experiment queue is full")
        try:
            manifest = create_manifest(load_dataset(db, body.dataset_id), body.config, body.token_ids)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        row = Experiment(id=manifest["experiment_id"], dataset_id=body.dataset_id, manifest=manifest, manifest_hash=digest(manifest), status="training", history=[{"state": "training", "at": now()}])
        db.add(row)
        db.commit()
        response = row_dict(row)
    pool.submit(execute, row.id, "training")
    return response

@router.get("/api/experiments/{id}")
def get(id: str):
    with SessionLocal() as db:
        row = db.get(Experiment, id)
        if not row:
            raise HTTPException(404, "Experiment not found")
        return row_dict(row)

@router.post("/api/experiments/{id}/freeze")
def freeze(id: str, body: EmptyInput | None = None):
    with SessionLocal() as db:
        changed = db.execute(update(Experiment).where(Experiment.id == id, Experiment.status == "trained", Experiment.frozen_hash.is_(None)).values(status="frozen", frozen_hash=Experiment.manifest_hash))
        if changed.rowcount != 1:
            raise HTTPException(409, "Only a trained attempt can be frozen; a frozen snapshot cannot be changed")
        row = db.get(Experiment, id)
        row.history = [*row.history, {"state": "frozen", "at": now()}]
        db.commit()
        return row_dict(row)

@router.post("/api/experiments/{id}/evaluate", status_code=202)
def evaluate(id: str, body: EmptyInput | None = None):
    with SessionLocal() as db:
        changed = db.execute(update(Experiment).where(Experiment.id == id, Experiment.status == "frozen", Experiment.frozen_hash.is_not(None)).values(status="evaluating"))
        if changed.rowcount != 1:
            raise HTTPException(409, "Holdout requires an unused frozen snapshot. Repeated evaluation is not a new independent test.")
        row = db.get(Experiment, id)
        row.history = [*row.history, {"state": "evaluating", "at": now()}]
        db.commit()
    pool.submit(execute, id, "holdout")
    return get(id)

@router.get("/api/experiments/{id}/bundle")
def bundle(id: str):
    with SessionLocal() as db:
        row = db.get(Experiment, id)
        if not row or not row.frozen_hash or not row.training:
            raise HTTPException(409, "Bundle requires a frozen trained experiment")
        try:
            value = verified_bundle_zip(load_dataset(db, row.dataset_id), row.manifest, {"training": row.training, "sensitivity": row.sensitivity}, row.holdout)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        return Response(value, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{id}-reproduction.zip"'})
