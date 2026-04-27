"""Search backend implementations.

Pluggable: every backend exposes a `search(query, n_results) -> list[Snippet]`
method. WebFactChecker picks one at construction.

v0.1 ships only Brave. Exa / DuckDuckGo land in v0.2.
"""
from truthcheck.backends.base import SearchBackend, Snippet
from truthcheck.backends.brave import BraveBackend

__all__ = ["BraveBackend", "SearchBackend", "Snippet"]
