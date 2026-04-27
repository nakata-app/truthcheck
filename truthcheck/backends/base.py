"""Common SearchBackend protocol that every implementation conforms to."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Snippet:
    """One search result extracted from a backend.

    Attributes:
        url: the canonical link.
        title: page title (when provided).
        snippet: short text excerpt — the substrate the verifier reads.
        domain_trust: 0.0–1.0, set by the caller when domain reputation
            is configured. Default 1.0 (trust all).
    """

    url: str
    title: str
    snippet: str
    domain_trust: float = 1.0


class SearchBackend(Protocol):
    """Every backend (Brave, Exa, DDG, …) exposes this surface."""

    name: str

    def search(self, query: str, n_results: int = 5) -> list[Snippet]:
        ...

    def estimate_cost_usd(self, n_calls: int = 1) -> float:
        ...
