import time
import httpx
from fastapi import APIRouter, Request, Query
from sqlalchemy import select, delete
from ..db import SessionLocal
from ..models import WalletObservation
from ..settings import settings
from .providers import address, signature, retrieved, LiveError, SolanaService, MarketDataService, WalletService, HttpProvider
from .auth import require_wallet, origin_for
from ..normalization import research_prices as normalize_prices, research_liquidity as normalize_liquidity

router = APIRouter(tags=["Real mainnet observations"])
# A single pooled client and shared service instances preserve caching across requests.
http = httpx.Client(timeout=10)
solana_service = SolanaService(settings, http)
market_service = MarketDataService(settings, http)
wallet_service = WalletService(solana_service, market_service)
history_http = HttpProvider(http)

def coverage(start, end):
    if not 1704067200 <= start < end <= int(time.time()) or end - start > 14 * 86400:
        raise LiveError(422, "Choose a past historical window of at most 14 days, after 2024-01-01.")

@router.get("/api/live/status")
def status():
    return {"network": "mainnet-beta", "kind": "REAL", "rpc": True, "rpc_provider": "configured RPC" if settings.solana_rpc_url else "Helius" if settings.helius_api_key else "public Solana RPC", "helius": bool(settings.helius_api_key), "birdeye": bool(settings.birdeye_api_key), "authentication": True, "history_provider": "Birdeye" if settings.birdeye_api_key else "CoinGecko / GeckoTerminal", "engine": "FastAPI and shared browser Python"}

@router.get("/api/markets/sol")
def sol():
    return market_service.sol()

@router.get("/api/markets/search")
def search(q: str = Query(min_length=1, max_length=80)):
    return market_service.search(q)

@router.get("/api/markets/{mint}")
def token(mint: str):
    return market_service.token(mint)

@router.get("/api/markets/{mint}/history")
def price_history(mint: str, days: int = 7):
    return market_service.history(mint, days)

@router.get("/api/wallets/{wallet}")
def wallet(wallet: str):
    return wallet_service.snapshot(wallet)

@router.get("/api/wallets/{wallet}/transactions")
def transactions(wallet: str, before: str | None = None):
    return solana_service.transactions(wallet, before)

@router.get("/api/wallets/{wallet}/observations")
def observations(wallet: str, request: Request):
    address(wallet)
    require_wallet(request, wallet)
    with SessionLocal() as db:
        rows = db.scalars(select(WalletObservation).where(WalletObservation.wallet == wallet).order_by(WalletObservation.ts.desc()).limit(2000)).all()
        return {"wallet": wallet, "kind": "REAL", "points": [{"ts": r.ts, "sol_balance": r.sol_balance, "valued_usd": r.valued_usd, "complete": r.complete} for r in rows[::-1]], "limitations": ["Actual saved observations since login, not reconstructed historical holdings.", "Missing quotes produce partial valued subtotals."]}

@router.post("/api/wallets/{wallet}/observations")
def observe(wallet: str, request: Request):
    address(wallet)
    origin_for(request)
    require_wallet(request, wallet)
    data = wallet_service.snapshot(wallet)
    from datetime import datetime
    ts = int(datetime.fromisoformat(data["retrieved_at"]).timestamp())
    identity = wallet + ":" + str(ts // 60)
    with SessionLocal() as db:
        if db.bind.dialect.name == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            from sqlalchemy.dialects.postgresql import insert
        statement = insert(WalletObservation).values(id=identity, wallet=wallet, ts=ts, sol_balance=data["sol_balance"], valued_usd=data["valued_subtotal_usd"], complete=int(data["portfolio_complete"]), payload=data).on_conflict_do_nothing(index_elements=["id"])
        db.execute(statement)
        db.execute(delete(WalletObservation).where(WalletObservation.wallet == wallet, WalletObservation.ts < int(time.time()) - 180 * 86400))
        db.commit()
    return {"saved": True, "observed_ts": ts}

@router.get("/api/wallets/{wallet}/history")
def history(wallet: str, start: int, end: int, before: str | None = None):
    address(wallet)
    coverage(start, end)
    if before:
        signature(before)
    if not settings.helius_api_key:
        raise LiveError(503, "HELIUS_API_KEY is not configured. Decoded historical swaps require Helius; RPC transfers are not treated as trades.")
    params = {"api-key": settings.helius_api_key, "gte-time": start, "lte-time": end, "limit": 100, "sort-order": "desc", "token-accounts": "balanceChanged", "commitment": "finalized"}
    if before:
        params["before-signature"] = before
    rows = history_http.request("GET", f"https://mainnet.helius-rpc.com/v0/addresses/{wallet}/transactions", "Helius history", params=params)
    if not isinstance(rows, list):
        raise LiveError(502, "Helius returned invalid historical transactions.")
    cursor = rows[-1].get("signature") if rows else None
    return {"wallet": wallet, "kind": "REAL", "provider": "Helius Enhanced Transactions", "retrieved_at": retrieved(), "transactions": rows, "next_cursor": cursor if cursor != before else None, "coverage_complete": not rows, "requested_start": start, "requested_end": end}

def birdeye(path, params):
    if not settings.birdeye_api_key:
        raise LiveError(503, "BIRDEYE_API_KEY is required for historical research prices and liquidity. Display charts are not executable research data.")
    result = history_http.request("GET", "https://public-api.birdeye.so" + path, "Birdeye research history", params=params, headers={"X-API-KEY": settings.birdeye_api_key, "x-chain": "solana"})
    if not result.get("success") or not isinstance(result.get("data"), dict):
        raise LiveError(503, "Historical data is unavailable for this token or API plan.")
    return result["data"]

@router.get("/api/markets/{mint}/research-prices")
def research_prices(mint: str, start: int, end: int):
    address(mint)
    coverage(start, end)
    if end - start > 300 * 98:
        raise LiveError(422, "Request at most 98 five-minute buckets per chunk.")
    data = birdeye("/defi/history_price", {"address": mint, "address_type": "token", "type": "5m", "time_from": start, "time_to": end, "ui_amount_mode": "raw"})
    if data.get("isScaledUiToken") or not isinstance(data.get("items"), list):
        raise LiveError(503, "Historical prices cannot be normalized safely.")
    try:
        prices = normalize_prices(data["items"], start, end)
    except ValueError as exc:
        raise LiveError(502, str(exc)) from None
    return {"kind": "REAL", "provider": "Birdeye", "mint": mint, "retrieved_at": retrieved(), "prices": prices}

@router.get("/api/markets/{mint}/research-liquidity")
def research_liquidity(mint: str, time: int):
    address(mint)
    if not 1704067200 <= time <= __import__("time").time():
        raise LiveError(422, "Invalid historical liquidity timestamp.")
    data = birdeye("/defi/v3/liquidity/history/token", {"address": mint, "resolution": "1m", "time": time, "direction": "back", "count": 100})
    if not isinstance(data.get("items"), list):
        raise LiveError(503, "Historical liquidity is unavailable.")
    try:
        items = normalize_liquidity(data["items"], time)
    except ValueError as exc:
        raise LiveError(502, str(exc)) from None
    return {"kind": "REAL", "provider": "Birdeye", "mint": mint, "retrieved_at": retrieved(), "items": items, "next_time": min(p["ts"] for p in items) - 1 if items else None}
