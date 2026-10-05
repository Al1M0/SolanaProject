/* The exact server Python engine executes here, off the browser's UI thread. */
let boot;
async function runtime() {
  if (!boot) boot = (async () => {
    importScripts("/runtime/pyodide.js");
    const py = await loadPyodide({indexURL:"/runtime/"});
    py.FS.mkdirTree("/home/pyodide/app");
    const files = ["__init__.py","domain.py","factors.py","strategies.py","metrics.py","quality.py","engine.py","demo.py","reports.py","normalization.py","analytics.py","audit.py","experiments.py","export_validation.py"];
    await Promise.all(files.map(async f => {
      const response = await fetch("/research/"+f);
      if (!response.ok) throw new Error("Shared engine source could not be loaded");
      py.FS.writeFile("/home/pyodide/app/"+f, await response.text());
    }));
    py.runPython("import json\nfrom app.demo import generate_demo\nfrom app.domain import StrategyConfig\nfrom app.engine import run_backtest, digest\nfrom app.quality import assess\nfrom app.reports import report_markdown\nfrom app.audit import run_audit, canonical_dataset\nfrom app.experiments import create_manifest, train_experiment, evaluate_experiment, bundle_base64\nfrom app.analytics import wallet_analytics, accumulation_events, build_real_dataset\ndemo = generate_demo()\n");
    return py;
  })();
  return boot;
}
self.onmessage = async ({data: message}) => {
  const {id, action, payload} = message;
  try {
    const py = await runtime();
    py.globals.set("payload_json", JSON.stringify(payload ?? {}));
    py.globals.set("progress_callback", value => self.postMessage({id,progress:value}));
    let value;
    if (action === "initialize") value = py.runPython("json.dumps({'dataset': {**{k:v for k,v in demo.items() if k != 'events'}, 'quality': assess(demo), 'content_hash': digest(demo)}, 'config': StrategyConfig().to_dict()})");
    else if (action === "run") value = py.runPython("args = json.loads(payload_json)\njson.dumps(run_backtest(args.get('dataset', demo), args.get('config', args), progress_callback), allow_nan=False)");
    else if (action === "audit") value = py.runPython("args = json.loads(payload_json)\njson.dumps(run_audit(args['dataset'], args['config'], args.get('tokens'), args.get('phase', 'training'), progress_callback), allow_nan=False)");
    else if (action === "dataset_quality") value = py.runPython("args = canonical_dataset(json.loads(payload_json))\njson.dumps({**args, 'quality': assess(args), 'content_hash': digest(args)}, allow_nan=False)");
    else if (action === "manifest") value = py.runPython("args = json.loads(payload_json)\nmanifest = create_manifest(args['dataset'], args['config'], args.get('tokens'))\njson.dumps({'manifest': manifest, 'manifest_json': json.dumps(manifest, sort_keys=True, separators=(',', ':'), allow_nan=False), 'manifest_hash': digest(manifest)})");
    else if (action === "train_experiment") value = py.runPython("args = json.loads(payload_json)\njson.dumps(train_experiment(args['dataset'], json.loads(args['manifest_json']) if args.get('manifest_json') else args['manifest'], progress_callback), allow_nan=False)");
    else if (action === "evaluate_experiment") value = py.runPython("args = json.loads(payload_json)\njson.dumps(evaluate_experiment(args['dataset'], json.loads(args['manifest_json']) if args.get('manifest_json') else args['manifest'], args['frozen_hash']), allow_nan=False)");
    else if (action === "bundle") value = JSON.stringify(py.runPython("from app.export_validation import verified_bundle_base64\nargs = json.loads(payload_json)\nverified_bundle_base64(args['dataset'], json.loads(args['manifest_json']) if args.get('manifest_json') else args['manifest'], args['trained'], args.get('holdout'), progress_callback)"));
    else if (action === "report") value = JSON.stringify(py.runPython("report_markdown(json.loads(payload_json))"));
    else if (action === "export_dataset") value = py.runPython("json.dumps(demo)");
    else if (action === "validate") value = py.runPython("json.dumps(StrategyConfig.from_dict(json.loads(payload_json)).to_dict())");
    else if (action === "analytics") value = py.runPython("args = json.loads(payload_json)\njson.dumps(wallet_analytics(args['histories'], args.get('minimum_sample', 10)), allow_nan=False)");
    else if (action === "accumulation") value = py.runPython("args = json.loads(payload_json)\njson.dumps(accumulation_events(args['histories'], StrategyConfig.from_dict(args.get('config', {})).to_dict()), allow_nan=False)");
    else if (action === "build_real") value = py.runPython("data = build_real_dataset(json.loads(payload_json))\njson.dumps({**data, 'quality': assess(data), 'content_hash': digest(data)}, allow_nan=False)");
    else throw new Error("Unsupported research command");
    self.postMessage({id, value:JSON.parse(value)});
  } catch (error) {self.postMessage({id,error:String(error.message || error)});}
};
