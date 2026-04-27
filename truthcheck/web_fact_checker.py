"""WebFactChecker — v0.1 working pipeline.

End-to-end:
  1. Split the input claim into atomic claims.
  2. For each, check the cache first.
  3. On miss: query the search backend, verify each snippet via NLI,
     aggregate into a Verdict, persist to cache.
  4. Combine atomic Verdicts into one final Verdict for the original
     input.

No LLM in the inference path. Backend choice (Brave default) and
verifier (NLI cross-encoder) are pluggable. Multi-source aggregation
follows Atakan's decision: contradicting sources → INCONCLUSIVE,
all sources surfaced.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from truthcheck.backends import BraveBackend, SearchBackend, Snippet
from truthcheck.cache import VerdictCache
from truthcheck.splitter import split_claims
from truthcheck.types import Source, Verdict, VerdictStatus
from truthcheck.verifier import NLIVerifier


_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "truthcheck"


class WebFactChecker:
    """Open-world fact verifier."""

    def __init__(
        self,
        backend: str | SearchBackend = "brave",
        api_key: str | None = None,
        trusted_domains: list[str] | None = None,
        cache_dir: str | None = None,
        ttl_seconds: int = 7 * 24 * 3600,
        verifier: NLIVerifier | None = None,
        n_sources: int = 5,
        support_threshold: float = 0.6,
        contradict_threshold: float = 0.4,
        dry_run: bool = False,
    ) -> None:
        if isinstance(backend, str):
            if backend == "brave":
                self.backend: SearchBackend = BraveBackend(api_key=api_key)
            else:
                raise ValueError(
                    f"Unknown backend '{backend}'. v0.1 ships only 'brave'. "
                    "Exa / DDG land in v0.2."
                )
        else:
            self.backend = backend

        self.trusted_domains = trusted_domains or []
        self.verifier = verifier or NLIVerifier()
        self.n_sources = n_sources
        self.support_threshold = support_threshold
        self.contradict_threshold = contradict_threshold
        self.dry_run = dry_run

        cache_path = Path(cache_dir or os.environ.get("TRUTHCHECK_CACHE") or _DEFAULT_CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)
        self._cache = VerdictCache(cache_path / "verdicts.db", ttl_seconds=ttl_seconds)

    def estimate_cost(self, claim: str) -> float:
        """Predict the USD cost of a check() call without running it.

        Splits the claim and multiplies per-call backend cost.
        """
        n = len(split_claims(claim)) or 1
        return self.backend.estimate_cost_usd(n)

    def check(self, claim: str, n_sources: int | None = None, **_: Any) -> Verdict:
        """Verify ``claim`` against the open web. Always returns a Verdict."""
        n_sources = n_sources or self.n_sources

        atomic = split_claims(claim) or [claim]
        atomic_verdicts: list[Verdict] = []

        total_cost = 0.0
        any_cache_hit = False

        for sub_claim in atomic:
            cached = self._cache.get(sub_claim, self.backend.name)
            if cached is not None:
                any_cache_hit = True
                cached.cache_hit = True
                atomic_verdicts.append(cached)
                continue

            if self.dry_run:
                # Don't issue real searches; estimate-only path.
                atomic_verdicts.append(
                    Verdict(
                        claim=sub_claim,
                        status=VerdictStatus.INCONCLUSIVE,
                        confidence=0.0,
                        cost_usd=self.backend.estimate_cost_usd(1),
                    )
                )
                total_cost += self.backend.estimate_cost_usd(1)
                continue

            t_start = time.time()
            snippets = self.backend.search(sub_claim, n_results=n_sources)
            sources = self._score_snippets(sub_claim, snippets)
            verdict = self._aggregate(sub_claim, sources)
            verdict.cost_usd = self.backend.estimate_cost_usd(1)
            verdict.as_of = t_start
            self._cache.put(sub_claim, self.backend.name, verdict)
            atomic_verdicts.append(verdict)
            total_cost += verdict.cost_usd

        # Combine atomic verdicts back into one verdict for the caller.
        return _combine_verdicts(claim, atomic_verdicts, atomic, total_cost, any_cache_hit)

    def _score_snippets(
        self, claim: str, snippets: list[Snippet]
    ) -> list[Source]:
        sources: list[Source] = []
        for snip in snippets:
            domain_trust = _domain_trust(snip.url, self.trusted_domains)
            entail = self.verifier.entail(snip.snippet, claim)
            sources.append(
                Source(
                    url=snip.url,
                    snippet=snip.snippet,
                    score=float(entail),
                    domain_trust=domain_trust,
                )
            )
        return sources

    def _aggregate(self, claim: str, sources: list[Source]) -> Verdict:
        if not sources:
            return Verdict(
                claim=claim,
                status=VerdictStatus.UNSUPPORTED,
                confidence=0.0,
            )

        # Weighted scores by domain trust.
        weighted = [s.score * s.domain_trust for s in sources]
        max_score = max(weighted)
        # Contradiction signal: sources with very low entailment AND a
        # claim-keyword in the snippet (so it's actually addressing the
        # claim and saying "no").
        contradicting = [
            s for s in sources
            if s.score < self.contradict_threshold and _addresses_claim(claim, s.snippet)
        ]
        supporting = [s for s in sources if s.score >= self.support_threshold]

        if supporting and contradicting:
            status = VerdictStatus.INCONCLUSIVE
            confidence = 0.5
        elif supporting:
            status = VerdictStatus.SUPPORTED
            confidence = max(weighted)
        elif contradicting:
            status = VerdictStatus.CONTRADICTED
            confidence = 1.0 - max_score
        else:
            status = VerdictStatus.UNSUPPORTED
            confidence = max_score

        return Verdict(
            claim=claim,
            status=status,
            confidence=float(confidence),
            sources=sources,
            atomic_claims=[claim],
        )


# ---- Helpers --------------------------------------------------------------

def _domain_trust(url: str, trusted: list[str]) -> float:
    """1.0 if url's host matches any trusted glob, else 0.7 (untrusted but allowed)."""
    if not trusted:
        return 1.0
    from fnmatch import fnmatch

    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
    except Exception:
        return 0.7
    for pattern in trusted:
        if fnmatch(host, pattern.lower()) or fnmatch(host, f"*.{pattern.lower()}"):
            return 1.0
    return 0.7


def _addresses_claim(claim: str, snippet: str) -> bool:
    """Cheap relevance check — does the snippet share content with the claim?"""
    import re

    claim_tokens = set(re.findall(r"\w+", claim.lower()))
    snippet_tokens = set(re.findall(r"\w+", snippet.lower()))
    if not claim_tokens:
        return False
    return (len(claim_tokens & snippet_tokens) / len(claim_tokens)) >= 0.3


def _combine_verdicts(
    original: str,
    parts: list[Verdict],
    atomic_strs: list[str],
    total_cost: float,
    any_cache_hit: bool,
) -> Verdict:
    """Combine N atomic verdicts into one verdict for the original claim."""
    if not parts:
        return Verdict(claim=original, status=VerdictStatus.INCONCLUSIVE, confidence=0.0)
    # Worst-status wins (CONTRADICTED > UNSUPPORTED > INCONCLUSIVE > SUPPORTED).
    rank = {
        VerdictStatus.SUPPORTED: 0,
        VerdictStatus.INCONCLUSIVE: 1,
        VerdictStatus.UNSUPPORTED: 2,
        VerdictStatus.CONTRADICTED: 3,
    }
    worst = max(parts, key=lambda v: rank[v.status])

    # Pool sources from all atomic verdicts; the caller can inspect.
    pooled: list[Source] = []
    for p in parts:
        pooled.extend(p.sources)

    avg_conf = sum(p.confidence for p in parts) / len(parts)

    return Verdict(
        claim=original,
        status=worst.status,
        confidence=float(avg_conf),
        sources=pooled,
        atomic_claims=atomic_strs,
        cost_usd=total_cost,
        cache_hit=any_cache_hit,
        as_of=time.time(),
    )
