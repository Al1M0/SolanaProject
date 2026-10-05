"""Optional real HTTP smoke test; never ships example responses as live application data."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import httpx

root = Path(__file__).resolve().parents[1]
process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8012"], cwd=root / "backend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
results = []
try:
    with httpx.Client(base_url="http://127.0.0.1:8012", trust_env=False, timeout=45) as client:
        for _ in range(200):
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if process.poll() is not None:
                raise RuntimeError("API exited before becoming healthy")
            time.sleep(.1)
        for endpoint in ["/health", "/api/live/status", "/api/markets/sol", "/api/markets/So11111111111111111111111111111111111111112/history?days=7", "/api/wallets/So11111111111111111111111111111111111111112", "/api/markets/search?q=JUP"]:
            response = client.get(endpoint)
            data = response.json()
            summary = {"endpoint": endpoint, "status": response.status_code}
            if response.status_code == 200:
                if "points" in data: summary.update(observations=len(data["points"]), provider=data.get("provider"))
                elif isinstance(data, list): summary.update(results=len(data))
                else: summary.update({k: data[k] for k in ("kind", "network", "sol_balance", "price_usd", "provider", "retrieved_at") if k in data})
            else:
                summary["detail"] = data.get("detail")
            results.append(summary)
            print(json.dumps(summary), flush=True)
        output = root / "docs/live-smoke.json"
        output.write_text(json.dumps({"checked_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "note": "Actual provider/HTTP checks at this time. These values are not used by the UI.", "checks": results}, indent=2))
finally:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
