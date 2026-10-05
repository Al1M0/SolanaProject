import base64
from datetime import datetime, timezone
import hashlib
import secrets
import time
from urllib.parse import urlparse
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update, delete, func
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from ..db import SessionLocal
from ..models import WalletNonce, WalletSession
from ..settings import settings
from .providers import address, decode58, LiveError

router = APIRouter(prefix="/api/auth", tags=["Wallet message authentication"])
COOKIE = "quant_wallet_session"
now = lambda: int(time.time())
hashed = lambda token: hashlib.sha256(token.encode()).hexdigest()

class NonceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wallet: str = Field(min_length=32, max_length=44)

class VerifyInput(NonceInput):
    id: str = Field(min_length=1, max_length=64)
    signature: str = Field(min_length=88, max_length=88)

def origin_for(request):
    origin = request.headers.get("origin", "")
    allowed = [x.strip().rstrip("/") for x in settings.cors_origins.split(",") if x.strip()]
    if origin not in allowed or (settings.app_origin and origin != settings.app_origin.rstrip("/")):
        raise LiveError(403, "This request must come from an allowed research terminal origin.")
    return origin

def current_session(request):
    token = request.cookies.get(COOKIE, "")
    if len(token) != 64:
        return None
    with SessionLocal() as db:
        row = db.get(WalletSession, hashed(token))
        return {"wallet": row.wallet, "expires_at": row.expires_at} if row and row.expires_at > now() else None

def require_wallet(request, wallet=None):
    session = current_session(request)
    if not session or (wallet and wallet != session["wallet"]):
        raise LiveError(401, "Sign a login message in Phantom to save this wallet's observations.")
    return session

@router.get("/session")
def session(request: Request):
    return {"session": current_session(request)}

@router.post("/nonce")
def nonce(body: NonceInput, request: Request):
    wallet, origin, ts = address(body.wallet), origin_for(request), now()
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(WalletNonce).where(WalletNonce.wallet == wallet, WalletNonce.issued_at > ts - 60))
        if count >= 5:
            raise LiveError(429, "Too many login requests. Wait a minute and retry.")
        nonce, identity = secrets.token_hex(32), secrets.token_hex(16)
        issued, expiry = (datetime.fromtimestamp(t, timezone.utc).isoformat() for t in (ts, ts + 300))
        message = f"{urlparse(origin).netloc} wants you to sign in with your Solana account:\n{wallet}\n\nSign in to Solana Quant Research Lab. This message authorizes a session only.\n\nURI: {origin}\nVersion: 1\nChain ID: solana:mainnet\nNonce: {nonce}\nIssued At: {issued}\nExpiration Time: {expiry}"
        db.execute(delete(WalletNonce).where(WalletNonce.expires_at < ts - 3600))
        db.execute(delete(WalletSession).where(WalletSession.expires_at < ts))
        db.add(WalletNonce(id=identity, wallet=wallet, nonce=nonce, message=message, origin=origin, issued_at=ts, expires_at=ts + 300, consumed=0))
        db.commit()
    return {"id": identity, "wallet": wallet, "message": message, "expires_at": ts + 300}

@router.post("/verify")
def verify(body: VerifyInput, request: Request, response: Response):
    wallet, origin = address(body.wallet), origin_for(request)
    with SessionLocal() as db:
        row = db.get(WalletNonce, body.id)
        if not row or row.wallet != wallet or row.origin != origin or row.consumed or row.expires_at <= now():
            raise LiveError(401, "Login challenge expired or already used. Request a new message.")
        valid = False
        try:
            encoded = base64.b64decode(body.signature, validate=True)
            if len(encoded) != 64:
                raise ValueError("Invalid signature size")
            Ed25519PublicKey.from_public_bytes(decode58(wallet)).verify(encoded, row.message.encode())
            valid = True
        except Exception:
            pass
        used = db.execute(update(WalletNonce).where(WalletNonce.id == body.id, WalletNonce.consumed == 0, WalletNonce.expires_at > now()).values(consumed=1)).rowcount
        if not valid or used != 1:
            db.commit()
            raise LiveError(401, "Message signature could not be verified. Request a new login message.")
        token, expires = secrets.token_hex(32), now() + 86400
        db.add(WalletSession(token_hash=hashed(token), wallet=wallet, expires_at=expires))
        db.commit()
    response.set_cookie(COOKIE, token, max_age=86400, httponly=True, secure=settings.session_cookie_secure or origin.startswith("https:"), samesite="lax", path="/")
    return {"wallet": wallet, "expires_at": expires}

@router.post("/logout")
def logout(request: Request, response: Response):
    origin_for(request)
    with SessionLocal() as db:
        db.execute(delete(WalletSession).where(WalletSession.token_hash == hashed(request.cookies.get(COOKIE, ""))))
        db.commit()
    response.delete_cookie(COOKIE, httponly=True, samesite="lax", secure=settings.session_cookie_secure, path="/")
    return {"ok": True}
