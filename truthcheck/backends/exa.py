"""Exa Search API wrapper.

Neural search REST endpoint, key via `x-api-key` header.
Docs: https://docs.exa.ai/reference/search-api-guide-for-coding-agents

Replaces Brave as the default backend after Brave's free tier was
removed. Snippet text is taken from per-result highlights so the
verifier has substrate to read.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any

from truthcheck.backends.base import Snippet


_EXA_ENDPOINT = "https://api.exa.ai/search"


class ExaBackend:
    """Exa Search REST client with a Snippet-shaped output."""

    name = "exa"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str = _EXA_ENDPOINT,
        timeout_s: float = 15.0,
        search_type: str = "auto",
        highlight_max_chars: int = 1000,
    ) -> None:
        if importlib.util.find_spec("requests") is None:
            raise SystemExit(
                'ExaBackend needs `requests`. Install with `pip install "truthcheck[exa]"`.'
            )
        self.api_key = api_key or os.environ.get("EXA_API_KEY")
        if not self.api_key:
            raise SystemExit(
                "EXA_API_KEY not set. Get a key at https://dashboard.exa.ai/api-keys"
            )
        self.endpoint = endpoint
        self.timeout_s = timeout_s
        self.search_type = search_type
        self.highlight_max_chars = highlight_max_chars

    def search(self, query: str, n_results: int = 5) -> list[Snippet]:
        import requests

        body: dict[str, Any] = {
            "query": query,
            "numResults": min(n_results, 25),
            "type": self.search_type,
            "contents": {
                "highlights": {"maxCharacters": self.highlight_max_chars},
            },
        }

        try:
            resp = requests.post(
                self.endpoint,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                },
                json=body,
                timeout=self.timeout_s,
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Exa Search request failed: {e}") from e

        if not resp.ok:
            raise RuntimeError(
                f"Exa Search returned {resp.status_code}: {resp.text[:200]}"
            )

        body_json = resp.json()
        results: list[dict[str, Any]] = body_json.get("results", [])
        snippets: list[Snippet] = []
        for r in results[:n_results]:
            snippets.append(
                Snippet(
                    url=str(r.get("url", "")),
                    title=str(r.get("title", "") or ""),
                    snippet=_extract_snippet(r),
                )
            )
        return snippets

    def estimate_cost_usd(self, n_calls: int = 1) -> float:
        # Exa /search auto pricing ~$0.005/call as of 2026-04;
        # actual cost varies with type (deep variants are pricier).
        return 0.005 * n_calls


def _extract_snippet(result: dict[str, Any]) -> str:
    """Pull readable text from an Exa result.

    Order of preference:
      1. joined `highlights` (token-efficient, query-relevant)
      2. `text` (when contents.text was requested)
      3. `summary` (when contents.summary was requested)
      4. empty string
    """
    highlights = result.get("highlights")
    if isinstance(highlights, list) and highlights:
        return " … ".join(str(h) for h in highlights if h)

    text = result.get("text")
    if isinstance(text, str) and text:
        return text

    summary = result.get("summary")
    if isinstance(summary, str) and summary:
        return summary

    return ""
