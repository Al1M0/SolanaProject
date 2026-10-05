"""Live endpoint access probes; configured keys alone never imply plan entitlement."""
from datetime import datetime, timezone
import httpx
from .base import ProviderError, RequestBudget, get_json
from ..settings import settings

WSOL = "So11111111111111111111111111111111111111112"
def check_readiness():
    now = int(datetime.now(timezone.utc).timestamp()) // 300 * 300 - 600
    checks = []
    budget = RequestBudget(6)
    with httpx.Client(timeout=10) as client:
        probes = [
            ("Helius decoded wallet history", settings.helius_api_key, f"https://mainnet.helius-rpc.com/v0/addresses/{WSOL}/transactions", {"api-key": settings.helius_api_key, "limit": 1, "gte-time": now-300, "lte-time": now}, None),
            ("Birdeye historical 5m price", settings.birdeye_api_key, "https://public-api.birdeye.so/defi/history_price", {"address": WSOL, "address_type": "token", "type": "5m", "time_from": now-300, "time_to": now, "ui_amount_mode": "raw"}, {"X-API-KEY": settings.birdeye_api_key, "x-chain": "solana"}),
            ("Birdeye historical exit liquidity", settings.birdeye_api_key, "https://public-api.birdeye.so/defi/v3/liquidity/history/token", {"address": WSOL, "resolution": "1m", "time": now, "direction": "back", "count": 1}, {"X-API-KEY": settings.birdeye_api_key, "x-chain": "solana"})]
        for name, key, url, params, headers in probes:
            if not key:
                checks.append({"endpoint": name, "status": "missing_key", "message": "HELIUS_API_KEY missing" if name.startswith("Helius") else "BIRDEYE_API_KEY missing"})
                continue
            try:
                result = get_json(client, url, params=params, headers=headers, attempts=2, budget=budget)
                ok = isinstance(result, list) if name.startswith("Helius") else isinstance(result, dict) and result.get("success") is True and isinstance(result.get("data", {}).get("items"), list)
                checks.append({"endpoint": name, "status": "accessible" if ok else "unverified", "message": "Endpoint responded; requested study coverage still must be verified" if ok else "Plan or response shape could not be verified"})
            except ProviderError as error:
                checks.append({"endpoint": name, "status": "blocked", "message": str(error)})
    return {"ready": all(c["status"] == "accessible" for c in checks), "checks": checks, "requests_used": budget.used,
        "checked_at": datetime.now(timezone.utc).isoformat(), "scope": "Endpoint access only; no assertion of complete history, account quota or redistribution rights"}
