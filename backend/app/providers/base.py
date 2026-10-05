from typing import Protocol
import time
import httpx


class ProviderError(RuntimeError):
    pass

class IngestionCancelled(ProviderError):
    pass

class RequestBudget:
    """Counts every HTTP attempt, including retries; cancellation checked between calls."""
    def __init__(self, limit=240, cancelled=None, progress=None):
        self.limit, self.used = limit, 0
        self.cancelled, self.progress = cancelled, progress

    def check(self):
        if self.cancelled and self.cancelled():
            raise IngestionCancelled("Ingestion cancelled. No partial dataset was published.")

    def consume(self):
        self.check()
        if self.used >= self.limit:
            raise ProviderError(f"Request budget exhausted ({self.used}/{self.limit}, including retries). Narrow the window or explicitly raise the budget.")
        self.used += 1
        if self.progress:
            self.progress(self.used, self.limit)


class HistoricalMarketProvider(Protocol):
    name: str
    def fetch(self, token: str, start: int, end: int, resolution: int = 300) -> tuple[list[dict], dict]: ...


def get_json(client, url, *, params=None, headers=None, attempts=5, sleep=time.sleep, budget=None):
    """Bounded backoff. Errors deliberately omit URLs, which may contain API keys."""
    for attempt in range(attempts):
        if budget:
            budget.consume()
        try:
            response = client.get(url, params=params, headers=headers)
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == attempts - 1:
                raise ProviderError("Provider network request failed after bounded retries") from None
            sleep(min(2 ** attempt, 16))
            continue
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == attempts - 1:
                raise ProviderError(f"Provider HTTP {response.status_code}; retry budget exhausted")
            try:
                delay = float(response.headers.get("Retry-After", 2 ** attempt))
            except ValueError:
                delay = 2 ** attempt
            sleep(max(0, min(delay, 8)))
            continue
        if response.status_code >= 400:
            raise ProviderError(f"Provider HTTP {response.status_code}; check API access, plan and request parameters")
        try:
            return response.json()
        except ValueError:
            raise ProviderError("Provider returned invalid JSON") from None
    raise ProviderError("Provider retry budget exhausted")
