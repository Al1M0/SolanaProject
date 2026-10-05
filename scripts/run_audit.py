#!/usr/bin/env python3
"""Reproducible untuned synthetic audit, or an authorized supplied dataset."""
import argparse
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from app.demo import generate_demo
from app.experiments import create_manifest, validate_snapshot, public_payload, train_experiment, evaluate_experiment, bundle_zip, research_report
from app.engine import digest
p=argparse.ArgumentParser()
p.add_argument('--dataset')
p.add_argument('--config')
p.add_argument('--manifest')
p.add_argument('--output',default=str(root/'research/reference'))
a=p.parse_args()
d=json.loads(Path(a.dataset).read_text()) if a.dataset else generate_demo()
c=json.loads(Path(a.config).read_text()) if a.config else {}
m=json.loads(Path(a.manifest).read_text()) if a.manifest else create_manifest(d,c)
validate_snapshot(m,d)
public_payload(m)
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
if (out/'manifest.json').exists():
    # Preserve the original reference and every subsequent CLI attempt.
    out=out/'attempts'/m['experiment_id']
    if out.exists():
        p.error('This immutable attempt already exists; reproduce its bundle or choose a new output directory')
    out.mkdir(parents=True)
def write_json(name,value):
    (out/(name+'.json')).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
write_json('manifest',m)
write_json('status',{'state':'training','experiment_id':m['experiment_id'],'mode':'offline CLI; no independent timestamp proof'})
try:
    trained=train_experiment(d,m)
    write_json('results',{**trained,'holdout':None})
    frozen_hash=digest(m)
    write_json('freeze',{'manifest_hash':frozen_hash,'mode':'offline CLI; no independent timestamp proof'})
    write_json('status',{'state':'evaluating','experiment_id':m['experiment_id']})
    holdout=evaluate_experiment(d,m,frozen_hash)
except Exception as error:
    write_json('status',{'state':'failed','experiment_id':m['experiment_id'],'error':str(error)})
    raise
for name,value in {'manifest':m,'results':{**trained,'holdout':holdout},'freeze':{'manifest_hash':frozen_hash,'mode':'offline CLI; no independent timestamp proof'},'summary':{phase:{key:{'metrics':s['metrics'],'activity':s['activity']} for key,s in result['results'].items()} for phase,result in [('training',trained['training']),('holdout',holdout)]}}.items():
    write_json(name,value)
(out/'research_report.md').write_text(research_report(m,trained['training'],holdout,trained['sensitivity']))
write_json('status',{'state':'evaluated','experiment_id':m['experiment_id']})
try:
    (out/'reproduction.zip').write_bytes(bundle_zip(d,m,trained,holdout))
except Exception as error:
    write_json('status',{'state':'export_failed','experiment_id':m['experiment_id'],'error':str(error)})
    raise
print(json.dumps({'experiment':m['experiment_id'],'kind':d['kind'],'manifest_hash':frozen_hash,'bundle':str(out/'reproduction.zip'),'holdout':{k:s['metrics']['net_return_pct'] for k,s in holdout['results'].items()}}))
