"""Skeleton WebFactChecker — public API surface, no working backend yet.

v0.0 is the "design document in code" stage:
- types are stable
- check() raises NotImplementedError with a helpful pointer
- subclassing for real backends is documented in ROADMAP.md

When v0.1 lands, this file gets the Brave / Exa / DuckDuckGo backend
plumbing and a real check() body. Until then, importing the class +
constructing it is allowed (no API calls happen at __init__) so
callers can write their integration code against the surface that
will exist.
"""
from __future__ import annotations

from typing import Any

from truthcheck.types import Verdict


class WebFactChecker:
    """Open-world fact verifier. **Skeleton — v0.1 will implement check().**

    Args:
        backend: search provider id ("brave", "exa", "ddg", "bing").
        api_key: backend API key. Falls back to a backend-specific env var.
        trusted_domains: glob patterns scored higher in aggregation.
        cache_dir: where to persist the claim → verdict cache.
        dry_run: when True, ``check()`` returns a cost estimate without
            spending API credit (useful in CI / preview environments).
    """

    def __init__(
        self,
        backend: str = "brave",
        api_key: str | None = None,
        trusted_domains: list[str] | None = None,
        cache_dir: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self.backend = backend
        self.api_key = api_key
        self.trusted_domains = trusted_domains or []
        self.cache_dir = cache_dir
        self.dry_run = dry_run

    def check(self, claim: str, n_sources: int = 5, **_: Any) -> Verdict:
        """Verify a claim against the open web.

        Args:
            claim: the natural-language statement to verify.
            n_sources: maximum number of search results to consider.

        Returns:
            A ``Verdict`` with status, confidence, sources, and cost.

        Raises:
            NotImplementedError: until v0.1 lands. See ROADMAP.md.
        """
        raise NotImplementedError(
            "truthcheck is at v0.0 — only types and the API surface are stable. "
            "v0.1 will ship the first backend. Track progress at "
            "https://github.com/nakata-app/truthcheck (when public)."
        )

    def estimate_cost(self, claim: str, n_sources: int = 5) -> float:
        """Predict the USD cost of a ``check()`` call without issuing one."""
        # Placeholder: real estimates plug in per-backend pricing tables.
        per_search = {"brave": 0.0001, "exa": 0.001, "ddg": 0.0, "bing": 0.0001}
        return per_search.get(self.backend, 0.0001)
