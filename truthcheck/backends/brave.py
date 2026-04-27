"""Brave Search API wrapper.

Free tier: 2000 queries/month, REST endpoint, key via header.
Docs: https://api.search.brave.com/app/documentation

Reasonable default backend — vendor neutral, no Google/Microsoft, high
quota among free options. Exa / DDG are v0.2 alternatives.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any

from truthcheck.backends.base import Snippet


_BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class BraveBackend:
    """Brave Search REST client with a Snippet-shaped output."""

    name = "brave"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str = _BRAVE_ENDPOINT,
        timeout_s: float = 10.0,
    ) -> None:
        if importlib.util.find_spec("requests") is None:
            raise SystemExit(
                'BraveBackend needs `requests`. Install with `pip install "truthcheck[brave]"`.'
            )
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY")
        if not self.api_key:
            raise SystemExit(
                "BRAVE_API_KEY not set. Get a free key at https://api.search.brave.com/"
            )
        self.endpoint = endpoint
        self.timeout_s = timeout_s

    def search(self, query: str, n_results: int = 5) -> list[Snippet]:
        import requests

        try:
            resp = requests.get(
                self.endpoint,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
                params={"q": query, "count": min(n_results, 20)},
                timeout=self.timeout_s,
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Brave Search request failed: {e}") from e

        if not resp.ok:
            raise RuntimeError(
                f"Brave Search returned {resp.status_code}: {resp.text[:200]}"
            )

        body = resp.json()
        results: list[dict[str, Any]] = body.get("web", {}).get("results", [])
        snippets: list[Snippet] = []
        for r in results[:n_results]:
            snippets.append(
                Snippet(
                    url=str(r.get("url", "")),
                    title=str(r.get("title", "")),
                    snippet=str(r.get("description", "")),
                )
            )
        return snippets

    def estimate_cost_usd(self, n_calls: int = 1) -> float:
        # Free tier covers ~2000/month; beyond that Brave's data
        # subscription tiers start ~$3 / 1000 calls. Budget the higher tier.
        return 0.003 * n_calls
