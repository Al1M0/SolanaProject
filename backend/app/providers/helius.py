"""Conservative Enhanced Transactions adapter, verified against official docs 2026-09-29.

Enhanced Transactions is a maintained legacy endpoint. Only explicit SWAP events
with unambiguous wallet-owned economic input/output legs are supported.
"""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math
import httpx
from .base import ProviderError, get_json

from ..normalization import normalize_swap, parse_amount, WSOL, USDC, USDT, QUOTES


class HeliusProvider:
    name = "helius-enhanced-transactions"
    def __init__(self, api_key, client=None, budget=None):
        if not api_key:
            raise ProviderError("HELIUS_API_KEY is not configured; no synthetic substitution was made")
        self.key = api_key
        self.client = client or httpx.Client(timeout=30)
        self.budget = budget

    def fetch_wallet(self, wallet, start, end, max_pages=20):
        before, seen, events, rejected = None, set(), [], Counter()
        complete = False
        duplicates = 0
        pages = 0
        raw_records = []
        for page in range(max_pages):
            params = {"api-key": self.key, "gte-time": start, "lte-time": end, "limit": 100,
                "sort-order": "desc", "token-accounts": "balanceChanged", "commitment": "finalized"}
            # Fetch all types and classify locally, avoiding type-filter continuation errors.
            if before:
                params["before-signature"] = before
            data = get_json(self.client, f"https://mainnet.helius-rpc.com/v0/addresses/{wallet}/transactions", params=params, budget=self.budget)
            pages += 1
            if not isinstance(data, list):
                raise ProviderError("Unexpected Helius history response; dataset was not fabricated")
            if not data:
                complete = True
                break
            for tx in data:
                signature = tx.get("signature")
                if signature in seen:
                    duplicates += 1
                    continue
                if not signature:
                    rejected["missing_signature"] += 1
                    continue
                seen.add(signature)
                raw_records.append(tx)
                if not isinstance(tx.get("timestamp"), int) or not start <= tx["timestamp"] <= end:
                    rejected["outside_requested_coverage"] += 1
                    continue
                normalized, reason = normalize_swap(tx, wallet)
                events.extend(normalized)
                if reason:
                    rejected[reason] += 1
            cursor = data[-1].get("signature")
            if not cursor or cursor == before:
                rejected["pagination_stalled"] += 1
                break
            before = cursor
        return events, {"wallet": wallet, "retrieved_at": datetime.now(timezone.utc).isoformat(), "pages": pages,
            "unique_transactions": len(seen), "duplicates_removed": duplicates, "rejected": dict(rejected),
            "coverage_complete": complete, "continuation_signature": before, "requested_start": start, "requested_end": end,
            "raw_transactions": raw_records}
