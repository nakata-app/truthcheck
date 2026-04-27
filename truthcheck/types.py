"""Public data types — stable contract surface for callers."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VerdictStatus(str, Enum):
    """High-level verdict the caller routes on."""

    SUPPORTED = "SUPPORTED"
    """Claim is corroborated by at least one trusted source."""

    UNSUPPORTED = "UNSUPPORTED"
    """No source either confirms or refutes the claim."""

    CONTRADICTED = "CONTRADICTED"
    """At least one trusted source explicitly refutes the claim."""

    INCONCLUSIVE = "INCONCLUSIVE"
    """Sources disagree, no clear majority, or claim is time-sensitive."""


@dataclass
class Source:
    """One piece of evidence considered when scoring a claim."""

    url: str
    snippet: str
    score: float  # 0.0–1.0 — entailment confidence for this source
    domain_trust: float = 1.0  # 0.0–1.0 — caller-configurable domain weight


@dataclass
class Verdict:
    """End-to-end fact-check result for a single claim."""

    claim: str
    status: VerdictStatus
    confidence: float  # 0.0–1.0 — aggregate over sources
    sources: list[Source] = field(default_factory=list)
    atomic_claims: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    cache_hit: bool = False
    as_of: float | None = None  # unix timestamp for time-sensitive claims
