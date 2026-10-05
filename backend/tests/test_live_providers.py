from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import time
import httpx
import pytest
from app.live.providers import MarketDataService, SolanaService, WalletService, LiveError, Cache, WSOL, MAINNET_GENESIS, address
from app.normalization import USDC

def settings():
    return SimpleNamespace(solana_rpc_url="https://rpc.test/", helius_api_key="", birdeye_api_key="", coingecko_demo_api_key="")

def token_account(raw="1200000", extension=None):
    info = {"mint": USDC, "tokenAmount": {"amount": raw, "decimals": 6}}
    if extension:
        info["extensions"] = [{"extension": extension}]
    return {"account": {"owner": "SPL", "data": {"parsed": {"info": info}}}}

def test_rpc_batch_sorted_by_id_and_exact_token_amounts():
    def handler(request):
        import json
        calls = json.loads(request.content)
        result = []
        for call in calls:
            method = call["method"]
            if method == "getGenesisHash": value = MAINNET_GENESIS
            elif method == "getBalance": value = {"value": 1234567890, "context": {"slot": 100}}
            else:
                standard = call["params"][1]["programId"].startswith("Tokenkeg")
                value = {"value": [token_account("1200000"), token_account("100000")] if standard else [token_account("200000", "scaledUiAmountConfig")]}
            result.append({"id": call["id"], "result": value})
        return httpx.Response(200, json=result[::-1])
    client = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
    data = SolanaService(settings(), client).balances(WSOL)
    assert data["sol_balance"] == 1.23456789 and data["kind"] == "REAL"
    assert len(data["tokens"]) == 1 and data["tokens"][0]["raw_amount"] == "1500000" and data["tokens"][0]["amount"] == "1.500000"
    assert not data["tokens"][0]["valuation_supported"]

def test_rpc_rejects_non_mainnet_and_invalid_public_address():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[{"id": 0, "result": "devnet-genesis"}])), trust_env=False)
    with pytest.raises(LiveError, match="mainnet-beta"):
        SolanaService(settings(), client).balances(WSOL)
    with pytest.raises(LiveError):
        address("z" * 44)

def test_market_quote_is_base_token_only_and_missing_fields_remain_null():
    pair = {"chainId": "solana", "baseToken": {"address": USDC, "symbol": "USDC"}, "priceUsd": "0.98", "liquidity": {"usd": 2000}, "volume": {"h24": 100}, "quoteToken": {"address": WSOL}}
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[pair])), trust_env=False)
    service = MarketDataService(settings(), client)
    data = service.tokens([USDC])[0]
    assert data["price_usd"] == .98 and data["market_cap_usd"] is None and data["name"] is None
    assert service.tokens([WSOL]) == []  # Never re-use a base token's price for its quote token.


def test_sol_denied_request_uses_actual_base_token_pool_with_visible_provenance():
    calls = []
    pair = {"chainId": "solana", "baseToken": {"address": WSOL, "symbol": "SOL"}, "priceUsd": "140", "liquidity": {"usd": 2000}, "pairAddress": "pool-fixture", "dexId": "fixture-dex"}
    def handler(request):
        calls.append(request.url.host)
        if request.url.host == "api.coingecko.com":
            return httpx.Response(403)
        return httpx.Response(200, json=[pair])
    service = MarketDataService(settings(), httpx.Client(transport=httpx.MockTransport(handler), trust_env=False))
    data = service.sol()
    assert calls == ["api.coingecko.com", "api.dexscreener.com"]  # Denials are not retried.
    assert data["price_usd"] == 140 and data["mint"] == WSOL and data["provider"] == "DEX Screener"
    assert data["pair_address"] == "pool-fixture" and data["market_cap_usd"] is None
    assert "HTTP 403" in data["limitations"][-1] and "instead of aggregated SOL" in data["limitations"][-1]


def test_sol_denied_and_only_quote_token_available_remains_unavailable():
    pair = {"chainId": "solana", "baseToken": {"address": USDC}, "quoteToken": {"address": WSOL}, "priceUsd": "1"}
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403) if r.url.host == "api.coingecko.com" else httpx.Response(200, json=[pair])), trust_env=False)
    with pytest.raises(LiveError, match="HTTP 403.*No usable wSOL") as error:
        MarketDataService(settings(), client).sol()
    assert error.value.status == 503


def test_configured_birdeye_sol_history_uses_only_closed_positive_observations(monkeypatch):
    monkeypatch.setattr("app.live.providers.time.time", lambda: 1767229200)
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"success": True, "data": {"items": [
            {"unixTime": 1767225600, "value": 140}, {"unixTime": 1767222000, "value": None},
            {"unixTime": 1767229200, "value": 150}, {"unixTime": 1767218400, "value": -1},
        ]}})
    s = settings(); s.birdeye_api_key = "unit-test-fixture"
    data = MarketDataService(s, httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)).history(WSOL, 1)
    assert len(calls) == 1 and calls[0].url.host == "public-api.birdeye.so"
    assert calls[0].url.params["address"] == WSOL and calls[0].url.params["type"] == "1H"
    assert data["provider"] == "Birdeye" and data["kind"] == "REAL"
    assert data["points"] == [{"ts": 1767229200, "price_usd": 140}]
    assert "historical liquidity" in data["limitations"][-1]

def test_partial_wallet_valuation_never_fills_unknown_prices():
    class Rpc:
        def balances(self, wallet):
            return {"wallet": wallet, "sol_balance": 2, "tokens": [{"mint": USDC, "amount": "4", "valuation_supported": True}, {"mint": WSOL, "amount": "2", "valuation_supported": False}], "kind": "REAL"}
    class Market:
        def sol(self): return {"price_usd": 100}
        def tokens(self, mints): return []
    data = WalletService(Rpc(), Market()).snapshot(WSOL)
    assert data["valued_subtotal_usd"] == 200 and not data["portfolio_complete"]
    assert data["unpriced_tokens"] == 2 and all(t["value_usd"] is None for t in data["tokens"])

def test_solana_fees_and_no_history_are_not_fabricated():
    import json
    def handler(request):
        result = []
        for c in json.loads(request.content):
            if c["method"] == "getGenesisHash": value = MAINNET_GENESIS
            elif c["method"] == "getSignaturesForAddress": value = [{"signature": "observed", "blockTime": None, "slot": 1, "err": None}]
            else: value = None
            result.append({"id": c["id"], "result": value})
        return httpx.Response(200, json=result)
    client = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
    transaction = SolanaService(settings(), client).transactions(WSOL)["transactions"][0]
    assert transaction["ts"] is None and transaction["type"] is None and transaction["fee_sol"] is None

def test_provider_rate_limit_and_timeout_errors_do_not_expose_key():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429)), trust_env=False)
    s = settings(); s.coingecko_demo_api_key = "test-secret-key"
    with pytest.raises(LiveError) as error:
        MarketDataService(s, client).sol()
    assert error.value.status == 429 and "test-secret-key" not in str(error.value)

def test_cache_deduplicates_parallel_calls_and_expires():
    cache, calls = Cache(), []
    def work():
        calls.append(1); time.sleep(.02); return 7
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert list(pool.map(lambda _: cache.get("one", .1, work), range(6))) == [7] * 6
    assert len(calls) == 1
    time.sleep(.11)
    assert cache.get("one", .1, work) == 7 and len(calls) == 2

def test_failed_requests_do_not_retain_locks_or_share_client_results():
    cache = Cache()
    for i in range(300):
        with pytest.raises(RuntimeError):
            cache.get(str(i), 1, lambda: (_ for _ in ()).throw(RuntimeError("provider failure")))
    assert not cache.locks and not cache.data
    first = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[{"id": 0, "result": MAINNET_GENESIS}])), trust_env=False)
    second = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[{"id": 0, "result": "devnet"}])), trust_env=False)
    SolanaService(settings(), first).mainnet()
    with pytest.raises(LiveError, match="mainnet-beta"):
        SolanaService(settings(), second).mainnet()

def test_live_routes_return_real_configuration_and_missing_credentials(client):
    assert client.get("/api/live/status").json()["network"] == "mainnet-beta"
    assert client.get("/api/wallets/invalid").status_code == 422
    assert client.get(f"/api/wallets/{WSOL}/history?start=1767225600&end=1767312000").status_code == 503
    assert client.get(f"/api/markets/{WSOL}/research-prices?start=1767225600&end=1767225900").status_code == 503


def test_research_prices_preserve_missing_values_and_delay_bucket_availability(client, monkeypatch):
    from app.live import routes
    start, end = 1767225600, 1767225900
    monkeypatch.setattr(routes, "birdeye", lambda *args: {"items": [{"unixTime": start, "value": 12}, {"unixTime": end, "value": None}]})
    response = client.get(f"/api/markets/{WSOL}/research-prices?start={start}&end={end}")
    assert response.status_code == 200 and response.json()["kind"] == "REAL"
    assert response.json()["prices"] == [
        {"ts": start + 300, "source_price_ts": start, "price_usd": 12},
        {"ts": end + 300, "source_price_ts": end, "price_usd": None},
    ]


@pytest.mark.parametrize("row", [None, {}, {"unixTime": "1767225600", "value": 1}, {"unixTime": 1767225601, "value": 1}, {"unixTime": 1767226200, "value": 1}, {"unixTime": 1767225600, "value": -1}])
def test_corrupt_historical_price_response_returns_502(client, monkeypatch, row):
    from app.live import routes
    monkeypatch.setattr(routes, "birdeye", lambda *args: {"items": [row]})
    response = client.get(f"/api/markets/{WSOL}/research-prices?start=1767225600&end=1767225900")
    assert response.status_code == 502
    assert "Historical provider" in response.json()["detail"]


@pytest.mark.parametrize("row, expected", [
    ({"unix_time": 1767225900, "exit_liquidity_usd": None, "liquidity_usd": 1000}, 200),
    ({"unix_time": 1767225960, "exit_liquidity_usd": 1000}, 502),
    ({"unix_time": 1767225900, "exit_liquidity_usd": -1}, 502),
])
def test_historical_liquidity_boundaries_and_unknown_depth(client, monkeypatch, row, expected):
    from app.live import routes
    monkeypatch.setattr(routes, "birdeye", lambda *args: {"items": [row]})
    response = client.get(f"/api/markets/{WSOL}/research-liquidity?time=1767225900")
    assert response.status_code == expected
    if expected == 200:
        assert response.json()["items"] == [{"ts": 1767225900, "liquidity_usd": None, "total_liquidity_usd": 1000}]
