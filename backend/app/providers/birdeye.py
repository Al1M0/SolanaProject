"""Historical USD prices and historical exit-liquidity snapshots, never latest data."""
from datetime import datetime, timezone
import httpx
import numpy as np
import pandas as pd
from .base import ProviderError, get_json
from ..normalization import research_prices, research_liquidity


class BirdeyeProvider:
    name = "birdeye-historical"
    def __init__(self, api_key, client=None, max_liquidity_pages=500, budget=None):
        if not api_key:
            raise ProviderError("BIRDEYE_API_KEY is not configured")
        self.client = client or httpx.Client(timeout=30)
        self.headers = {"X-API-KEY": api_key, "x-chain": "solana"}
        self.max_liquidity_pages = max_liquidity_pages
        self.budget = budget

    def _data(self, path, params):
        value = get_json(self.client, "https://public-api.birdeye.so" + path, params=params, headers=self.headers, budget=self.budget)
        if not isinstance(value, dict) or value.get("success") is not True or not isinstance(value.get("data"), dict):
            raise ProviderError("Birdeye did not return a successful historical-data response")
        return value["data"]

    def fetch(self, token, start, end, resolution=300):
        if resolution != 300:
            raise ProviderError("This MVP verifies and supports 5-minute price observations only")
        if start < 1704067200:
            raise ProviderError("Birdeye documents historical liquidity coverage from 2024-01-01")
        prices, liquidity, warnings = [], [], []
        # Small bounded chunks avoid assuming an undocumented page size for history_price.
        for left in range(start - resolution, end, resolution * 99):
            right = min(left + resolution * 98, end - resolution)
            data = self._data("/defi/history_price", {"address": token, "address_type": "token", "type": "5m", "time_from": left, "time_to": right, "ui_amount_mode": "raw"})
            if data.get("isScaledUiToken"):
                raise ProviderError("Scaled-UI tokens require an explicit normalization model and are not supported")
            try:
                prices.extend(research_prices(data.get("items", []), left, right))
            except ValueError as exc:
                raise ProviderError(str(exc)) from None
        anchor = end
        completed = False
        for _ in range(self.max_liquidity_pages):
            data = self._data("/defi/v3/liquidity/history/token", {"address": token, "resolution": "1m", "time": anchor, "direction": "back", "count": 100})
            items = data.get("items", [])
            if not items:
                break
            try:
                liquidity.extend(research_liquidity(items, anchor))
                oldest = min(x["ts"] for x in research_liquidity(items, anchor))
            except ValueError as exc:
                raise ProviderError(str(exc)) from None
            if oldest <= start:
                completed = True
                break
            if oldest >= anchor:
                warnings.append("Historical liquidity pagination did not advance")
                break
            anchor = oldest - 1
        if not completed:
            warnings.append("Historical liquidity backfill did not reach the requested start")
        # Exact grid join only. No interpolation, backward fill or current-liquidity substitution.
        grid = pd.DataFrame({"ts": range(start, end + 1, resolution)})
        for records, columns in ((prices, ["price_usd", "source_price_ts"]), (liquidity, ["liquidity_usd", "total_liquidity_usd"])):
            frame = pd.DataFrame(records)
            if frame.empty:
                for column in columns:
                    grid[column] = np.nan
            else:
                if frame.duplicated("ts").any():
                    conflicts = frame.groupby("ts")[columns[0]].nunique().gt(1).any()
                    if conflicts:
                        raise ProviderError("Conflicting duplicate historical observations")
                grid = grid.merge(frame.drop_duplicates("ts"), on="ts", how="left", validate="one_to_one")
        grid = grid.replace([np.inf, -np.inf], np.nan)
        events = []
        for row in grid.to_dict("records"):
            def finite(key):
                v = row.get(key)
                return float(v) if v is not None and pd.notna(v) and np.isfinite(v) else None
            events.append({"id": f"birdeye:{token}:{int(row['ts'])}", "type": "market", "ts": int(row["ts"]), "token": token,
                "price_usd": finite("price_usd"), "liquidity_usd": finite("liquidity_usd"), "total_liquidity_usd": finite("total_liquidity_usd"),
                "source_price_ts": finite("source_price_ts"), "volume_usd": None, "provider": self.name})
        return events, {"provider": self.name, "retrieved_at": datetime.now(timezone.utc).isoformat(), "resolution_seconds": resolution,
            "requested_start": start, "requested_end": end, "price_observations": len(prices), "liquidity_observations": len(liquidity),
            "price_availability_lag_seconds": resolution, "liquidity_field": "exit_liquidity_usd", "liquidity_resolution_seconds": 60,
            "missing_prices": sum(e["price_usd"] is None for e in events), "missing_liquidity": sum(e["liquidity_usd"] is None for e in events), "warnings": warnings}
