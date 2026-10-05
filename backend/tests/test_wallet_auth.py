import base64
import time
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import select
from app.live.providers import BASE58
from app.models import WalletNonce, WalletSession
from app.db import SessionLocal

ORIGIN = {"Origin": "http://localhost:3000"}
def encode58(raw):
    value, result = int.from_bytes(raw, "big"), ""
    while value:
        value, digit = divmod(value, 58)
        result = BASE58[digit] + result
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + result

def identity():
    private = Ed25519PrivateKey.generate()
    return private, encode58(private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))

def challenge(client, wallet):
    response = client.post("/api/auth/nonce", json={"wallet": wallet}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    return response.json()

def verification(key, nonce):
    return {"id": nonce["id"], "wallet": nonce["wallet"], "signature": base64.b64encode(key.sign(nonce["message"].encode())).decode()}

def test_signed_login_session_hashed_cookie_replay_and_logout(client):
    key, wallet = identity()
    nonce = challenge(client, wallet)
    assert wallet in nonce["message"] and "solana:mainnet" in nonce["message"] and "localhost:3000" in nonce["message"]
    payload = verification(key, nonce)
    response = client.post("/api/auth/verify", json=payload, headers=ORIGIN)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "max-age=86400" in cookie
    assert client.get("/api/auth/session").json()["session"]["wallet"] == wallet
    with SessionLocal() as db:
        stored = db.scalar(select(WalletSession).where(WalletSession.wallet == wallet))
        assert stored.token_hash != client.cookies.get("quant_wallet_session")
        assert db.get(WalletNonce, nonce["id"]).consumed == 1
    assert client.post("/api/auth/verify", json=payload, headers=ORIGIN).status_code == 401
    assert client.post("/api/auth/logout", json={}, headers=ORIGIN).status_code == 200
    assert client.get("/api/auth/session").json()["session"] is None

def test_auth_rejects_missing_origin_wrong_origin_bad_address_and_expired_nonce(client):
    key, wallet = identity()
    assert client.post("/api/auth/nonce", json={"wallet": wallet}).status_code == 403
    assert client.post("/api/auth/nonce", json={"wallet": wallet}, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert client.post("/api/auth/nonce", json={"wallet": "z" * 44}, headers=ORIGIN).status_code == 422
    nonce = challenge(client, wallet)
    with SessionLocal() as db:
        db.get(WalletNonce, nonce["id"]).expires_at = int(time.time()) - 1
        db.commit()
    assert client.post("/api/auth/verify", json=verification(key, nonce), headers=ORIGIN).status_code == 401

def test_bad_signature_consumes_nonce_and_wallet_substitution_fails(client):
    key, wallet = identity()
    other, other_wallet = identity()
    nonce = challenge(client, wallet)
    payload = verification(key, nonce)
    payload["wallet"] = other_wallet
    assert client.post("/api/auth/verify", json=payload, headers=ORIGIN).status_code == 401
    payload = verification(other, nonce)
    assert client.post("/api/auth/verify", json=payload, headers=ORIGIN).status_code == 401
    assert client.post("/api/auth/verify", json=verification(key, nonce), headers=ORIGIN).status_code == 401

def test_auth_nonce_has_bounded_rate_and_atomic_replay_protection(client):
    key, wallet = identity()
    nonce = challenge(client, wallet)
    for _ in range(4):
        challenge(client, wallet)
    assert client.post("/api/auth/nonce", json={"wallet": wallet}, headers=ORIGIN).status_code == 429
    payload = verification(key, nonce)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post("/api/auth/verify", json=payload, headers=ORIGIN), range(2)))
    assert sorted(r.status_code for r in responses) == [200, 401]

def test_wallet_observations_require_signed_owner_and_ignore_client_prices(client, monkeypatch):
    from app.live import routes
    key, wallet = identity()
    _, other_wallet = identity()
    assert client.get(f"/api/wallets/{wallet}/observations").status_code == 401
    nonce = challenge(client, wallet)
    assert client.post("/api/auth/verify", json=verification(key, nonce), headers=ORIGIN).status_code == 200
    assert client.get(f"/api/wallets/{other_wallet}/observations").status_code == 401
    assert client.post(f"/api/wallets/{wallet}/observations", json={}).status_code == 403
    monkeypatch.setattr(routes.wallet_service, "snapshot", lambda w: {"wallet": w, "sol_balance": 2.0, "valued_subtotal_usd": 250.0, "portfolio_complete": False, "retrieved_at": "2026-10-03T08:00:00+00:00"})
    for _ in range(2):
        assert client.post(f"/api/wallets/{wallet}/observations", json={"value_usd": 999999}, headers=ORIGIN).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(f"/api/wallets/{wallet}/observations", json={}, headers=ORIGIN), range(2)))
    assert all(r.status_code == 200 for r in responses)
    data = client.get(f"/api/wallets/{wallet}/observations").json()
    assert len(data["points"]) == 1 and data["points"][0]["valued_usd"] == 250 and data["points"][0]["complete"] == 0

def test_cors_allows_credentials_only_for_explicit_terminal_origin(client):
    response = client.options("/api/auth/nonce", headers={**ORIGIN, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"})
    assert response.headers["access-control-allow-origin"] == ORIGIN["Origin"]
    assert response.headers["access-control-allow-credentials"] == "true"
    other = client.options("/api/auth/nonce", headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in other.headers
