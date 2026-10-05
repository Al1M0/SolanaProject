import copy
import json
import subprocess
import sys
import time
from io import BytesIO
import zipfile
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.demo import generate_demo
from app.engine import digest
from app.experiments import create_manifest, train_experiment, evaluate_experiment, bundle_zip, sensitivity, validate_snapshot
from app.domain import ResearchDataError
from app.export_validation import verified_bundle_zip, same_values

@pytest.fixture
def experiment():
    data=generate_demo(days=4)
    manifest=create_manifest(data, {}, created_at="2026-10-03T00:00:00+00:00", attempt_nonce="fixture")
    trained=train_experiment(data, manifest)
    return data,manifest,trained

def test_manifest_hash_configuration_and_engine_are_enforced(experiment):
    d,m,_=experiment
    with pytest.raises(ResearchDataError,match="frozen"):
        evaluate_experiment(d,m,None)
    tampered=copy.deepcopy(m);tampered["configuration"]["fee_bps"]=0
    with pytest.raises(ResearchDataError,match="frozen"):
        evaluate_experiment(d,tampered,digest(m))
    changed=copy.deepcopy(d);changed["events"][0]["price_usd"]*=2
    with pytest.raises(ResearchDataError,match="dataset content hash"):
        validate_snapshot(m,changed)
    assert create_manifest(d,{"fee_bps":40},created_at=m["created_at"],attempt_nonce="fixture")["experiment_id"]!=m["experiment_id"]

def test_sensitivity_never_reads_holdout(experiment):
    d,m,trained=experiment
    changed=copy.deepcopy(d)
    for e in changed["events"]:
        if e["ts"]>=m["split"]["holdout_start"] and e["type"]=="market":
            e["price_usd"]*=100
    changed_manifest=create_manifest(changed,m["configuration"],m["token_universe"],m["created_at"],m["attempt_nonce"])
    assert sensitivity(changed,changed_manifest)==trained["sensitivity"]
    assert len(trained["sensitivity"]["rows"])==7
    assert all(r["end_ts"]<m["split"]["holdout_start"] for r in trained["sensitivity"]["rows"])

def test_export_reproduces_every_result_and_refuses_credentials(experiment,tmp_path):
    d,m,trained=experiment
    holdout=evaluate_experiment(d,m,digest(m))
    archive=bundle_zip(d,m,trained,holdout)
    assert archive==bundle_zip(d,m,trained,holdout)
    with zipfile.ZipFile(BytesIO(archive)) as z:
        assert z.testzip() is None
        assert {"manifest.json","dataset.json","results.json","trades.json","exclusions.json","research_report.md","reproduce.py","checksums.json"}<=set(z.namelist())
        z.extractall(tmp_path)
    run=subprocess.run([sys.executable,"reproduce.py"],cwd=tmp_path,text=True,capture_output=True,timeout=30)
    assert run.returncode==0,run.stderr+run.stdout
    assert json.loads(run.stdout)["reproduced"]
    bad=copy.deepcopy(d);bad["provenance"]["api_key"]="never-export-me"
    bm=create_manifest(bad,{})
    with pytest.raises(ValueError,match="credential"):
        bundle_zip(bad,bm,trained)

def test_unconfirmed_real_redistribution_omits_dataset(experiment):
    d,m,trained=experiment
    # Export-policy fixture only; this is not a genuine REAL study.
    data=copy.deepcopy(d);data["kind"]="REAL";data["provenance"]["redistribution"]="not_confirmed"
    manifest=create_manifest(data,{})
    adjusted=copy.deepcopy(trained);adjusted["training"]["dataset_hash"]=manifest["dataset_content_hash"]
    with zipfile.ZipFile(BytesIO(bundle_zip(data,manifest,adjusted))) as z:
        assert "dataset.json" not in z.namelist()
        assert "DATASET_NOT_REDISTRIBUTED.txt" in z.namelist()

def wait(client,id):
    for _ in range(120):
        e=client.get("/api/experiments/"+id).json()
        if e["status"] not in ("training","evaluating"):
            return e
        time.sleep(.1)
    pytest.fail("Experiment did not complete")

def test_persisted_freeze_no_repeated_holdout_and_all_attempts_retained(client):
    tokens=[t["mint"] for t in client.get("/api/datasets/synthetic-seed-33").json()["tokens"]]
    body={"dataset_id":"synthetic-seed-33","config":{},"token_ids":tokens}
    e=client.post("/api/experiments",json=body).json()
    assert client.post(f"/api/experiments/{e['id']}/evaluate",json={}).status_code==409
    trained=wait(client,e["id"]);assert trained["status"]=="trained",trained
    frozen=client.post(f"/api/experiments/{e['id']}/freeze",json={}).json()
    assert frozen["frozen_hash"]==digest(frozen["manifest"])
    assert client.post(f"/api/experiments/{e['id']}/freeze",json={}).status_code==409
    assert client.post(f"/api/experiments/{e['id']}/evaluate",json={"fee_bps":0}).status_code==422
    from app.db import SessionLocal
    with SessionLocal() as db:
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE experiments SET manifest_hash = 'changed' WHERE id = :id"),{"id":e["id"]});db.commit()
        db.rollback()
    assert client.post(f"/api/experiments/{e['id']}/evaluate",json={}).status_code==202
    assert wait(client,e["id"])["status"]=="evaluated"
    assert client.post(f"/api/experiments/{e['id']}/evaluate",json={}).status_code==409
    archive=client.get(f"/api/experiments/{e['id']}/bundle")
    assert archive.status_code==200
    bad=generate_demo(days=4);bad["id"]="failed-attempt-fixture";next(x for x in bad["events"] if x["type"]=="market")["price_usd"]=None
    assert client.post("/api/datasets",json=bad).status_code==201
    second=client.post("/api/experiments",json={**body,"dataset_id":bad["id"]}).json()
    assert wait(client,second["id"])["status"]=="training_failed"
    assert {e["id"],second["id"]}<={r["id"] for r in client.get("/api/experiments").json()}

def test_equivalent_json_number_types_produce_the_same_frozen_configuration():
    from app.domain import StrategyConfig
    a=StrategyConfig.from_dict({'warmup_hours':24.0,'fee_bps':30})
    b=StrategyConfig.from_dict({'warmup_hours':24,'fee_bps':30.0})
    assert type(a.warmup_hours) is int and a.to_dict()==b.to_dict()
    d=generate_demo(days=4)
    ma=create_manifest(d,a.to_dict(),created_at='fixture',attempt_nonce='same')
    mb=create_manifest(d,b.to_dict(),created_at='fixture',attempt_nonce='same')
    assert digest(ma)==digest(mb)
    assert train_experiment(d,ma)['training']['phase']=='training'


def test_browser_number_roundtrip_export_passes_strict_offline_reproduction(experiment, tmp_path):
    d, m, trained = experiment
    holdout = evaluate_experiment(d, m, digest(m))
    def browser_numbers(v):
        if isinstance(v, dict): return {k: browser_numbers(x) for k, x in v.items()}
        if isinstance(v, list): return [browser_numbers(x) for x in v]
        return int(v) if type(v) is float and v.is_integer() else v
    saved = browser_numbers({**trained, "holdout": holdout})
    assert digest(saved) != digest({**trained, "holdout": holdout}), "regression fixture must exercise the lost float representation"
    progress = []
    archive = verified_bundle_zip(d, m, {k: saved[k] for k in ("training", "sensitivity")}, saved["holdout"], progress.append)
    with zipfile.ZipFile(BytesIO(archive)) as z:
        assert json.loads(z.read("manifest.json")) == m
        assert json.loads(z.read("results.json")) == saved
        z.extractall(tmp_path)
    run = subprocess.run([sys.executable, "reproduce.py"], cwd=tmp_path, text=True, capture_output=True, timeout=30)
    assert run.returncode == 0, run.stderr + run.stdout
    assert json.loads(run.stdout)["reproduced"] and progress[-1] == 100


def test_export_rerun_rejects_a_changed_result_without_numeric_tolerance(experiment):
    d, m, trained = experiment
    changed = copy.deepcopy(trained)
    changed["training"]["results"]["strategy"]["metrics"]["net_return_pct"] += 1e-10
    with pytest.raises(ResearchDataError, match="saved results differ"):
        verified_bundle_zip(d, m, changed)
    assert not same_values({"n": 1}, {"n": True})
    assert not same_values({"n": 0}, {"n": None})
    assert same_values({"n": 1000.0}, {"n": 1000})
