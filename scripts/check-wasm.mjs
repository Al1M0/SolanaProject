// Execute the same Python modules in WebAssembly, then compare to native CPython.
import {loadPyodide} from "../frontend/node_modules/pyodide/pyodide.mjs";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {execFileSync} from "node:child_process";
import assert from "node:assert/strict";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const py=await loadPyodide();
py.FS.mkdirTree("/home/pyodide/app");
for(const file of ["__init__.py","domain.py","factors.py","strategies.py","metrics.py","quality.py","engine.py","demo.py","reports.py","normalization.py","analytics.py","audit.py","experiments.py","export_validation.py"])
  py.FS.writeFile("/home/pyodide/app/"+file,fs.readFileSync(path.join(root,"backend/app",file),"utf8"));
const code="from app.demo import generate_demo\nfrom app.engine import run_backtest\nimport json\nprint(json.dumps(run_backtest(generate_demo(), {}), allow_nan=False))";
const python=process.env.QUANT_PYTHON || path.join(root,".venv/bin/python");
const native=JSON.parse(execFileSync(python,["-c",code],{env:{...process.env,PYTHONPATH:path.join(root,"backend")},maxBuffer:10*1024*1024,encoding:"utf8"}));
const wasm=JSON.parse(py.runPython(code.replace("print(json.dumps(","json.dumps(").replace("allow_nan=False))","allow_nan=False)")));
assert.equal(native.fingerprint,wasm.fingerprint);
for(const segment of ["in_sample","out_of_sample"]){
  assert.equal(native[segment].trades.length,wasm[segment].trades.length);
  for(const key of ["net_return_pct","gross_return_pct","max_drawdown_pct","costs_usd"])
    assert.ok(Math.abs(native[segment].metrics[key]-wasm[segment].metrics[key])<1e-8,`${segment} ${key}`);
}
console.log(JSON.stringify({check:"Native / WebAssembly parity",passed:true,fingerprint:wasm.fingerprint,out_of_sample:wasm.out_of_sample.metrics}));

const analyticCode=`from app.analytics import wallet_analytics, accumulation_events, build_real_dataset
from app.normalization import USDC
from app.quality import assess
import json
def tx(wallet,ts,side,amount):
    token={"userAccount":wallet,"mint":"fixture-token","rawTokenAmount":{"tokenAmount":"1000000","decimals":6}}
    quote={"userAccount":wallet,"mint":USDC,"rawTokenAmount":{"tokenAmount":str(amount*1000000),"decimals":6}}
    return {"signature":f"fixture-{wallet}-{ts}","timestamp":ts,"slot":ts,"type":"SWAP","transactionError":None,"events":{"swap":{"tokenInputs":[quote if side=="buy" else token],"tokenOutputs":[token if side=="buy" else quote]}}}
histories=[{"wallet":w,"requested_start":0,"requested_end":1200,"coverage_complete":True,"provider":"parity test fixture","transactions":[tx(w,1,"buy",10),tx(w,2,"sell",12),tx(w,600,"buy",10)]} for w in ("A","B","C")]
d=build_real_dataset({"id":"parity-fixture-real","start_ts":0,"end_ts":1200,"retrieved_at":"fixture","histories":histories})
print(json.dumps({"analytics":wallet_analytics(histories),"detections":accumulation_events(histories,{"min_closed_trades":1,"min_wallet_count":3}),"quality":assess(d)},allow_nan=False))`;
const nativeAnalytics=JSON.parse(execFileSync(python,["-c",analyticCode],{env:{...process.env,PYTHONPATH:path.join(root,"backend")},encoding:"utf8"}));
const wasmAnalytics=JSON.parse(py.runPython(analyticCode.replace("print(json.dumps(","json.dumps(").replace("allow_nan=False))","allow_nan=False)")));
assert.deepEqual(nativeAnalytics,wasmAnalytics);assert.equal(wasmAnalytics.detections.events.length,1);assert.equal(wasmAnalytics.quality.performance_ready,false);
console.log(JSON.stringify({check:"Wallet analysis, accumulation and missing-data gating parity (fixtures)",passed:true}));

const auditCode=`from app.demo import generate_demo
from app.experiments import create_manifest, train_experiment, evaluate_experiment, bundle_files
from app.engine import digest
import json
d=generate_demo(days=4)
m=create_manifest(d,{},created_at="2026-10-03T00:00:00+00:00",attempt_nonce="wasm-parity-fixture")
t=train_experiment(d,m)
h=evaluate_experiment(d,m,digest(m))
files=bundle_files(d,m,t,h)
print(json.dumps({'manifest':m,'trained':t,'holdout':h,'bundle_files':sorted(files),'result_hash':digest({'trained':t,'holdout':h})},allow_nan=False))`;
const nativeAudit=JSON.parse(execFileSync(python,["-c",auditCode],{env:{...process.env,PYTHONPATH:path.join(root,"backend")},maxBuffer:20*1024*1024,encoding:"utf8"}));
const wasmAudit=JSON.parse(py.runPython(auditCode.replace("print(json.dumps(","json.dumps(").replace("allow_nan=False))","allow_nan=False)")));
assert.deepEqual(nativeAudit.manifest,wasmAudit.manifest);
for(const phase of ["trained","holdout"]){
  const nativeResults=phase==="trained"?nativeAudit.trained.training:nativeAudit.holdout;
  const wasmResults=phase==="trained"?wasmAudit.trained.training:wasmAudit.holdout;
  assert.equal(nativeResults.fingerprint,wasmResults.fingerprint);
  for(const k of ["strategy","buy_and_hold","momentum"]){assert.equal(nativeResults.results[k].trades.length,wasmResults.results[k].trades.length);for(const key of ["net_return_pct","gross_return_pct","costs_usd","max_drawdown_pct"])assert.ok(Math.abs(nativeResults.results[k].metrics[key]-wasmResults.results[k].metrics[key])<1e-8,`${phase} ${k} ${key}`);}
}
assert.deepEqual(nativeAudit.trained.sensitivity.rows.map(r=>r.fingerprint),wasmAudit.trained.sensitivity.rows.map(r=>r.fingerprint));assert.deepEqual(nativeAudit.bundle_files,wasmAudit.bundle_files);assert.equal(nativeAudit.result_hash,wasmAudit.result_hash);
const zip=py.runPython("from app.experiments import bundle_base64\nbundle_base64(d,m,t,h)");assert.ok(zip.length>1000);
console.log(JSON.stringify({check:"Frozen audit, both benchmarks, training-only sensitivity and export source parity",passed:true,manifest_hash:nativeAudit.manifest.dataset_content_hash}));

// Exercise the actual JSON boundary: the browser turns Python 1000.0 into JS 1000.
py.globals.set("browser_dataset_json",JSON.stringify(JSON.parse(py.runPython("json.dumps(d)"))));
const browserSaved=JSON.parse(py.runPython("browser_d=json.loads(browser_dataset_json)\nbrowser_m=create_manifest(browser_d,{},created_at='2026-10-04T00:00:00+00:00',attempt_nonce='browser-roundtrip-fixture')\nbrowser_t=train_experiment(browser_d,browser_m)\nbrowser_h=evaluate_experiment(browser_d,browser_m,digest(browser_m))\njson.dumps({'trained':browser_t,'holdout':browser_h},allow_nan=False)"));
const exportPayload={dataset:JSON.parse(py.runPython("json.dumps(browser_d)")),manifest_json:py.runPython("json.dumps(browser_m,sort_keys=True,separators=(',',':'))"),trained:browserSaved.trained,holdout:browserSaved.holdout};
py.globals.set("export_payload_json",JSON.stringify(exportPayload));
let verifiedZip;
try{verifiedZip=py.runPython("from app.export_validation import verified_bundle_base64\na=json.loads(export_payload_json)\nverified_bundle_base64(a['dataset'],json.loads(a['manifest_json']),a['trained'],a['holdout'])");}catch(error){console.error(String(error));process.exit(1);}
const reproduced=JSON.parse(execFileSync(python,["-c",`import sys,tempfile,zipfile,subprocess,json
from io import BytesIO
with tempfile.TemporaryDirectory(prefix='quant-browser-export-') as directory:
    with zipfile.ZipFile(BytesIO(sys.stdin.buffer.read())) as archive:
        archive.extractall(directory)
    run=subprocess.run([sys.executable,'reproduce.py'],cwd=directory,text=True,capture_output=True,timeout=30)
    if run.returncode: raise SystemExit(run.stderr+run.stdout)
    print(run.stdout)`],{input:Buffer.from(verifiedZip,"base64"),encoding:"utf8",timeout:45000}));
assert.equal(reproduced.reproduced,true);
assert.equal(reproduced.results_hash,py.runPython("digest({**browser_t,'holdout':browser_h})"));
console.log(JSON.stringify({check:"Browser JSON roundtrip export passes strict native offline reproduction",passed:true,experiment_id:reproduced.experiment_id}));
