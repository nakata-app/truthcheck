"""Search backend implementations.

Pluggable: every backend exposes a `search(query, n_results) -> list[Snippet]`
method. WebFactChecker picks one at construction.

v0.1 default: Exa (Brave's free tier was removed in 2026-04).
Brave is retained for users with a paid key. DDG / SearXNG are v0.2.
"""
from truthcheck.backends.base import SearchBackend, Snippet
from truthcheck.backends.brave import BraveBackend
from truthcheck.backends.exa import ExaBackend

__all__ = ["BraveBackend", "ExaBackend", "SearchBackend", "Snippet"]
