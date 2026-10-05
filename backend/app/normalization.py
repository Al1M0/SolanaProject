"""Portable conservative swap parser shared by FastAPI and the browser research worker."""
from decimal import Decimal, InvalidOperation
import math

WSOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
QUOTES = {WSOL, USDC, USDT}


def historical_rows(items):
    if not isinstance(items, list) or any(not isinstance(row, dict) for row in items):
        raise ValueError("Historical provider returned invalid observations.")
    return items


def historical_time(value, first, last, resolution):
    if type(value) is not int or not first <= value <= last or value % resolution:
        raise ValueError("Historical provider returned an invalid or out-of-window timestamp.")
    return value


def historical_number(value):
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError, OverflowError):
        return None


def research_prices(items, start, end):
    prices = []
    for row in historical_rows(items):
        ts = historical_time(row.get("unixTime"), start, end, 300)
        price = historical_number(row.get("value"))
        if price is not None and price <= 0:
            raise ValueError("Historical provider returned a non-positive token price.")
        prices.append({"ts": ts + 300, "source_price_ts": ts, "price_usd": price})
    return prices


def research_liquidity(items, anchor):
    observations = []
    for row in historical_rows(items):
        ts = historical_time(row.get("unix_time"), 1704067200, anchor, 60)
        depth = historical_number(row.get("exit_liquidity_usd"))
        total = historical_number(row.get("liquidity_usd"))
        if any(value is not None and value < 0 for value in (depth, total)):
            raise ValueError("Historical provider returned negative liquidity.")
        observations.append({"ts": ts, "liquidity_usd": depth, "total_liquidity_usd": total})
    return observations


def parse_amount(leg):
    raw = leg.get("rawTokenAmount")
    if not isinstance(raw, dict) or not isinstance(raw.get("decimals"), int) or not 0 <= raw["decimals"] <= 18:
        raise ValueError("missing_decimals")
    try:
        amount = Decimal(str(raw["tokenAmount"])) / (Decimal(10) ** raw["decimals"])
    except (InvalidOperation, KeyError):
        raise ValueError("invalid_amount") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("invalid_amount")
    return float(amount), raw["decimals"], str(raw["tokenAmount"])


def normalize_swap(tx, wallet):
    if tx.get("transactionError") is not None:
        return [], "failed_transaction"
    if tx.get("type") != "SWAP":
        return [], "not_supported_swap"
    swap = (tx.get("events") or {}).get("swap")
    if not isinstance(swap, dict):
        return [], "missing_swap_event"
    if not tx.get("signature") or not isinstance(tx.get("timestamp"), int) or not isinstance(tx.get("slot"), int):
        return [], "missing_identity_or_time"
    try:
        def legs(key, native_key):
            result = []
            for leg in swap.get(key) or []:
                if leg.get("userAccount") != wallet:
                    continue
                amount, decimals, raw = parse_amount(leg)
                if not leg.get("mint"):
                    raise ValueError("missing_mint")
                result.append({"mint": leg["mint"], "amount": amount, "decimals": decimals, "raw": raw})
            native = swap.get(native_key)
            if native and native.get("account") == wallet:
                amount = float(Decimal(str(native["amount"])) / Decimal(1_000_000_000))
                if not math.isfinite(amount) or amount <= 0:
                    raise ValueError("invalid_native_amount")
                result.append({"mint": WSOL, "amount": amount, "decimals": 9, "raw": str(native["amount"])})
            return result
        inputs, outputs = legs("tokenInputs", "nativeInput"), legs("tokenOutputs", "nativeOutput")
    except (ValueError, KeyError, TypeError, InvalidOperation):
        return [], "invalid_or_missing_amounts"
    # Economic endpoints only. Never count inner route hops as wallet accumulation.
    if len(inputs) != 1 or len(outputs) != 1:
        return [], "ambiguous_wallet_legs"
    i, o = inputs[0], outputs[0]
    if i["mint"] in QUOTES and o["mint"] not in QUOTES:
        token, quote, side = o, i, "buy"
    elif o["mint"] in QUOTES and i["mint"] not in QUOTES:
        token, quote, side = i, o, "sell"
    else:
        return [], "unsupported_quote_pair"
    return [{"id": f"{tx['signature']}:{wallet}:{token['mint']}:{side}", "signature": tx["signature"],
        "type": "swap", "ts": tx["timestamp"], "slot": tx["slot"], "wallet": wallet,
        "token": token["mint"], "side": side, "quantity": token["amount"], "decimals": token["decimals"],
        "raw_quantity": token["raw"], "quote_mint": quote["mint"], "quote_quantity": quote["amount"],
        "quote_price": quote["amount"] / token["amount"], "execution_price_usd": None,
        "price_source": "unavailable; quote units are not assumed to be USD", "network_fee_lamports": tx.get("fee"),
        "provider": "helius-enhanced-transactions", "dex_source": tx.get("source")}], None
