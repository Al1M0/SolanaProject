"""Actual local HTTP train/freeze/holdout/export/reproduce integration check."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile
from io import BytesIO
import httpx
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='quant-audit-http-') as temp:
    env={**os.environ,'DATABASE_URL':'sqlite:///'+str(Path(temp)/'study.db'),'SEED_DEMO':'true','API_TOKEN':''}
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=env,check=True)
    server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8013'],cwd=root/'backend',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    checks=[]
    try:
        with httpx.Client(base_url='http://127.0.0.1:8013',trust_env=False,timeout=30) as client:
            for _ in range(150):
                try:
                    if client.get('/health').status_code==200:break
                except httpx.HTTPError:pass
                if server.poll() is not None:raise RuntimeError('Audit server exited')
                time.sleep(.1)
            d=client.get('/api/datasets/synthetic-seed-33').json()
            r=client.post('/api/experiments',json={'dataset_id':d['id'],'config':{},'token_ids':[t['mint'] for t in d['tokens']]});r.raise_for_status();e=r.json();id=e['id'];checks.append({'step':'create training','status':r.status_code,'kind':e['manifest']['dataset_kind']})
            def wait():
                for _ in range(200):
                    row=client.get('/api/experiments/'+id).json()
                    if row['status'] not in ('training','evaluating'):return row
                    time.sleep(.1)
                raise RuntimeError('Audit timed out')
            assert wait()['status']=='trained'
            r=client.post('/api/experiments/'+id+'/freeze',json={});r.raise_for_status();assert r.json()['frozen_hash']==e['manifest_hash'];checks.append({'step':'freeze exact snapshot','status':r.status_code})
            r=client.post('/api/experiments/'+id+'/evaluate',json={});r.raise_for_status();result=wait();assert result['status']=='evaluated';checks.append({'step':'holdout vs both benchmarks','status':r.status_code})
            assert client.post('/api/experiments/'+id+'/evaluate',json={}).status_code==409
            archive=client.get('/api/experiments/'+id+'/bundle');archive.raise_for_status()
            out=Path(temp)/'bundle';out.mkdir()
            with zipfile.ZipFile(BytesIO(archive.content)) as z:assert z.testzip() is None;z.extractall(out)
            run=subprocess.run([sys.executable,'reproduce.py'],cwd=out,check=True,capture_output=True,text=True,timeout=30)
            reproduced=json.loads(run.stdout);assert reproduced['reproduced'];checks.append({'step':'ZIP independent subprocess reproduction','passed':True})
            record={'checked_at':datetime.now(timezone.utc).isoformat(),'mode':'actual local HTTP + fresh SQLite, SYNTHETIC observations','experiment_id':id,'manifest_hash':e['manifest_hash'],'results_hash':reproduced['results_hash'],'checks':checks}
            (root/'docs/audit-http-smoke.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait()
