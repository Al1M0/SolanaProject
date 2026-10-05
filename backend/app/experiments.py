"""Frozen manifests, training-only pre-specified sensitivity and portable exports."""
import base64
import copy
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import re
import uuid
import zipfile
from .audit import BENCHMARKS, bounds, canonical_dataset, run_audit, select_universe
from .domain import StrategyConfig, ResearchDataError
from .engine import digest, ENGINE_VERSION

PORTABLE_FILES = ("__init__.py", "domain.py", "factors.py", "strategies.py", "metrics.py", "quality.py", "engine.py", "demo.py", "reports.py", "normalization.py", "analytics.py", "audit.py", "experiments.py")
SENSITIVITY_RULE = {"design": "Seven pre-specified one-at-a-time rows; base plus low/high fees, delay and unique-wallet threshold. Training only; no best-row selection.",
    "fees": "base / 2, min(1000, base * 2 + 10)", "delays_minutes": "max(0, base - 5), min(1440, base + 5)", "unique_buyers": "max(1, base - 1), min(100, base + 1)"}

def source_files():
    root = Path(__file__).parent
    return {f: (root / f).read_text(encoding="utf-8") for f in PORTABLE_FILES}

def source_revision():
    return "source-sha256:" + digest(source_files())

def now():
    return datetime.now(timezone.utc).isoformat()

def create_manifest(dataset, config, tokens=None, created_at=None, attempt_nonce=None):
    c = StrategyConfig.from_dict(config)
    _, tokens = select_universe(dataset, tokens)
    manifest = {"schema_version": 1, "created_at": created_at or now(), "attempt_nonce": attempt_nonce or uuid.uuid4().hex,
        "hypothesis": c.hypothesis, "dataset_id": dataset["id"], "dataset_kind": dataset["kind"],
        "dataset_content_hash": digest(canonical_dataset(dataset)), "provider_provenance": copy.deepcopy(dataset["provenance"]),
        "wallet_universe": list(c.wallet_ids or dataset["wallets"]), "token_universe": tokens, "configuration": c.to_dict(),
        "execution_assumptions": {k: c.to_dict()[k] for k in ("initial_capital_usd", "position_size_usd", "entry_delay_minutes", "fee_bps", "slippage_bps", "fixed_fee_usd", "liquidity_impact_bps_per_pct", "min_liquidity_usd", "max_liquidity_participation_pct")},
        "observation_availability": "5m REAL prices available source_price_ts + 300s; exact historical liquidity snapshots; no gap filling. SYNTHETIC observations are simulated.",
        "split": bounds(dataset, c), "benchmarks": copy.deepcopy(BENCHMARKS), "sensitivity_design": SENSITIVITY_RULE,
        "seed": dataset.get("provenance", {}).get("seed"), "engine_version": ENGINE_VERSION, "source_revision": source_revision(),
        "holdout_warning": "Historical holdout may already be known from raw data. This lock protects the stored snapshot, not secrecy or absence of human look-ahead."}
    manifest["experiment_id"] = "exp_" + digest(manifest)[:24]
    return manifest

def validate_snapshot(manifest, dataset):
    if digest(canonical_dataset(dataset)) != manifest["dataset_content_hash"]:
        raise ResearchDataError("Immutable dataset content hash mismatch")
    if manifest["source_revision"] != source_revision() or manifest["engine_version"] != ENGINE_VERSION:
        raise ResearchDataError("Engine source revision mismatch; use the exported engine for reproduction")
    expected = create_manifest(dataset, manifest["configuration"], manifest["token_universe"], manifest["created_at"], manifest["attempt_nonce"])
    if expected != manifest:
        raise ResearchDataError("Manifest does not match its immutable configuration, universe or experiment identifier")

def sensitivity(dataset, manifest, progress=None):
    validate_snapshot(manifest, dataset)
    c = manifest["configuration"]
    grid = [("base", {}), ("fee_low", {"fee_bps": c["fee_bps"] / 2}), ("fee_high", {"fee_bps": min(1000, c["fee_bps"] * 2 + 10)}),
        ("delay_low", {"entry_delay_minutes": max(0, c["entry_delay_minutes"] - 5)}), ("delay_high", {"entry_delay_minutes": min(1440, c["entry_delay_minutes"] + 5)}),
        ("buyers_low", {"min_wallet_count": max(1, c["min_wallet_count"] - 1)}), ("buyers_high", {"min_wallet_count": min(100, c["min_wallet_count"] + 1)})]
    rows = []
    for i, (label, changes) in enumerate(grid):
        # run_audit(training) discards all events at/after the split before computing factors.
        result = run_audit(dataset, {**c, **changes}, manifest["token_universe"], "training")
        s = result["results"]["strategy"]
        rows.append({"row": label, "changes": changes, "phase": "training", "end_ts": result["split"]["training_end"], "metrics": s["metrics"], "fingerprint": result["fingerprint"]})
        if progress:
            progress((i+1)*100//len(grid))
    return {"design": SENSITIVITY_RULE, "rows": rows, "selection": "No automated selection; freeze the user's current configuration, not the best row"}

def train_experiment(dataset, manifest, progress=None):
    validate_snapshot(manifest, dataset)
    return {"training": run_audit(dataset, manifest["configuration"], manifest["token_universe"], "training"), "sensitivity": sensitivity(dataset, manifest, progress)}

def evaluate_experiment(dataset, manifest, frozen_hash):
    if not frozen_hash or digest(manifest) != frozen_hash:
        raise ResearchDataError("Holdout requires the exact persisted frozen manifest hash")
    validate_snapshot(manifest, dataset)
    return run_audit(dataset, manifest["configuration"], manifest["token_universe"], "holdout")

def research_report(manifest, training, holdout, sensitivity_result):
    lines = ["# Hypothesis audit", "", f"Experiment: `{manifest['experiment_id']}`", f"Dataset: **{manifest['dataset_kind']}**", f"Hypothesis: {manifest['hypothesis']}",
        f"Dataset SHA-256: `{manifest['dataset_content_hash']}`", f"Frozen manifest SHA-256: `{digest(manifest)}`", f"Engine: `{manifest['source_revision']}`", "", manifest["holdout_warning"]]
    for name, result in (("Training", training), ("Historical holdout", holdout)):
        lines += ["", "## " + name]
        if not result:
            lines.append("Not evaluated. No performance claim.")
            continue
        lines += ["", "| Portfolio | Gross % | Net % | Costs USD | Trades | Exposure % | Turnover | Failed |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for key, s in result["results"].items():
            m, a = s["metrics"], s["activity"]
            def number(v):
                return "N/A" if v is None else f"{v:.4f}"
            lines.append(f"| {key} | {number(m['gross_return_pct'])} | {number(m['net_return_pct'])} | {number(m['costs_usd'])} | {m['trade_count']} | {number(a['time_weighted_exposure_pct'])} | {number(a['round_trip_turnover_x'])} | {a['failed_execution_count']} |")
        lines += ["", *["- " + f for f in result["findings"]], "", *["- " + f for f in result["limitations"]]]
    lines += ["", "## Sensitivity", "Training-only pre-specified grid. All rows retained; no holdout optimization.", "```json", json.dumps(sensitivity_result, indent=2, allow_nan=False), "```", "", "## Benchmark definitions", json.dumps(manifest["benchmarks"], indent=2)]
    return "\n".join(lines) + "\n"

def public_payload(value):
    """Refuse potentially credential-bearing payloads rather than silently changing hashes."""
    if isinstance(value, dict):
        for key, val in value.items():
            if re.search(r"api.?key|authorization|cookie|password|private.?key|session.?token|secret", str(key), re.I):
                raise ValueError("Export blocked: credential-like field in research payload")
            public_payload(val)
    elif isinstance(value, list):
        for val in value:
            public_payload(val)
    elif isinstance(value, str) and re.search(r"[?&](?:api[-_]?key|token|secret)=|Bearer\s+\S+", value, re.I):
        raise ValueError("Export blocked: credential-like URL or authorization value")

REPRODUCE = '''"""Offline reproduction; standard-library Python 3.10+. No provider requests."""
import argparse, json
from pathlib import Path
from app.engine import digest
from app.experiments import validate_snapshot, train_experiment, evaluate_experiment
p=argparse.ArgumentParser()
p.add_argument('--dataset', help='Authorized original dataset if redistribution was not permitted')
a=p.parse_args()
root=Path(__file__).parent
checks=json.loads((root/'checksums.json').read_text())
import hashlib
for name, expected in checks.items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
        raise SystemExit('Bundle checksum mismatch: '+name)
m=json.loads((root/'manifest.json').read_text())
path=Path(a.dataset) if a.dataset else root/'dataset.json'
if not path.exists():
    raise SystemExit('Dataset excluded due to unconfirmed redistribution rights. Supply --dataset /authorized/original.json')
d=json.loads(path.read_text())
validate_snapshot(m,d)
expected=json.loads((root/'results.json').read_text())
actual=train_experiment(d,m)
actual['holdout']=evaluate_experiment(d,m,digest(m)) if expected.get('holdout') else None
if digest(actual)!=digest(expected):
    raise SystemExit('Result mismatch; exact fingerprints and all results must match')
print(json.dumps({'reproduced':True,'experiment_id':m['experiment_id'],'manifest_hash':digest(m),'results_hash':digest(actual)}))
'''

def bundle_files(dataset, manifest, trained, holdout=None):
    validate_snapshot(manifest, dataset)
    payload = {**trained, "holdout": holdout}
    public_payload([canonical_dataset(dataset), manifest, payload])
    if holdout and holdout["dataset_hash"] != manifest["dataset_content_hash"]:
        raise ResearchDataError("Holdout does not match frozen dataset")
    permitted = dataset["kind"] == "SYNTHETIC" or dataset.get("provenance", {}).get("redistribution") == "permitted"
    def encoded(v):
        return json.dumps(v, indent=2, sort_keys=True, allow_nan=False) + "\n"
    results = [r for r in (trained["training"], holdout) if r]
    if any(r["dataset_hash"] != manifest["dataset_content_hash"] for r in results):
        raise ResearchDataError("Export results do not match the immutable dataset")
    files = {"manifest.json": encoded(manifest), "configuration.json": encoded(manifest["configuration"]), "results.json": encoded(payload),
        "provenance.json": encoded(manifest["provider_provenance"]), "trades.json": encoded({r["phase"]: {k:s["trades"] for k,s in r["results"].items()} for r in results}),
        "exclusions.json": encoded({r["phase"]: {"quality": r["quality"], "portfolios": {k:s["skipped"] for k,s in r["results"].items()}} for r in results}),
        "research_report.md": research_report(manifest, trained["training"], holdout, trained["sensitivity"]), "reproduce.py": REPRODUCE,
        "README.md": "# Reproduction bundle\n\nRun `python3 reproduce.py` (Python 3.10+, standard library only).\n\n" + ("SYNTHETIC normalized observations included. These are not genuine Solana performance.\n" if permitted and dataset["kind"] == "SYNTHETIC" else "Provider observations included only when redistribution provenance explicitly permits it. Otherwise use `python3 reproduce.py --dataset /authorized/original.json`.\n") + "\nThe script verifies source, dataset, manifest and exact results. Hashes prove consistency, not accuracy, profitability or an unseen historical holdout. No credentials are included.\n"}
    if permitted:
        files["dataset.json"] = encoded(canonical_dataset(dataset))
    else:
        files["DATASET_NOT_REDISTRIBUTED.txt"] = "Redistribution rights not confirmed. Obtain the original dataset through authorized access and verify its manifest SHA-256.\n"
    files.update({"app/" + f: content for f, content in source_files().items()})
    import hashlib
    files["checksums.json"] = encoded({name: hashlib.sha256(text.encode()).hexdigest() for name, text in files.items()})
    return files

def bundle_zip(dataset, manifest, trained, holdout=None):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for filename, text in sorted(bundle_files(dataset, manifest, trained, holdout).items()):
            info = zipfile.ZipInfo(filename, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, text)
    return buffer.getvalue()

def bundle_base64(*args):
    return base64.b64encode(bundle_zip(*args)).decode()
