"""truthcheck v0.1 — tests for splitter / cache / verifier / web_fact_checker.

Backend HTTP calls are monkey-patched, so tests run without a Brave
key or network. The real Brave smoke is a separate manual job.
"""
from __future__ import annotations

from typing import Any

import pytest


def test_imports_and_version():
    import truthcheck

    assert truthcheck.__version__ == "0.1.0"
    assert truthcheck.WebFactChecker is not None
    assert truthcheck.Verdict is not None
    assert truthcheck.Source is not None
    assert truthcheck.VerdictStatus is not None


def test_verdict_status_enum_values():
    from truthcheck import VerdictStatus

    assert VerdictStatus.SUPPORTED.value == "SUPPORTED"
    assert VerdictStatus.UNSUPPORTED.value == "UNSUPPORTED"
    assert VerdictStatus.CONTRADICTED.value == "CONTRADICTED"
    assert VerdictStatus.INCONCLUSIVE.value == "INCONCLUSIVE"


def test_verdict_dataclass_round_trip():
    from truthcheck import Source, Verdict, VerdictStatus

    v = Verdict(
        claim="x",
        status=VerdictStatus.SUPPORTED,
        confidence=0.9,
        sources=[Source(url="https://example.com", snippet="...", score=0.91)],
        atomic_claims=["x"],
        cost_usd=0.001,
    )
    assert v.status == VerdictStatus.SUPPORTED
    assert v.sources[0].domain_trust == 1.0


# ---- Splitter -----------------------------------------------------------


def test_splitter_single_sentence_returns_one_claim():
    from truthcheck.splitter import split_claims

    assert split_claims("Türkiye'nin başkenti Ankara.") == ["Türkiye'nin başkenti Ankara"]


def test_splitter_breaks_on_sentence_boundary():
    from truthcheck.splitter import split_claims

    parts = split_claims("İstanbul büyük bir şehirdir. Ankara başkenttir.")
    assert "İstanbul büyük bir şehirdir" in parts
    assert "Ankara başkenttir" in parts


def test_splitter_breaks_comma_separated_facts():
    from truthcheck.splitter import split_claims

    parts = split_claims("Türkiye nüfusu 85 milyon, 81 il var.")
    assert "Türkiye nüfusu 85 milyon" in parts
    assert "81 il var" in parts


def test_splitter_returns_empty_for_blank_input():
    from truthcheck.splitter import split_claims

    assert split_claims("") == []
    assert split_claims("   \n\t  ") == []


# ---- Cache --------------------------------------------------------------


def test_cache_round_trip(tmp_path):
    from truthcheck import Verdict, VerdictStatus
    from truthcheck.cache import VerdictCache

    cache = VerdictCache(tmp_path / "cache.db")
    v = Verdict(claim="hi", status=VerdictStatus.SUPPORTED, confidence=0.9)
    cache.put("hi", "brave", v)
    loaded = cache.get("hi", "brave")
    assert loaded is not None
    assert loaded.confidence == pytest.approx(0.9)


def test_cache_returns_none_for_unknown_claim(tmp_path):
    from truthcheck.cache import VerdictCache

    cache = VerdictCache(tmp_path / "cache.db")
    assert cache.get("unknown", "brave") is None


def test_cache_expires_past_ttl(tmp_path):
    """A cached verdict older than ttl_seconds is treated as a miss."""
    import time as _time

    from truthcheck import Verdict, VerdictStatus
    from truthcheck.cache import VerdictCache

    cache = VerdictCache(tmp_path / "cache.db", ttl_seconds=1)
    cache.put("x", "brave", Verdict(claim="x", status=VerdictStatus.SUPPORTED, confidence=0.5))
    _time.sleep(1.1)
    assert cache.get("x", "brave") is None


def test_cache_keys_isolate_backends(tmp_path):
    """Same claim under different backends cache separately."""
    from truthcheck import Verdict, VerdictStatus
    from truthcheck.cache import VerdictCache

    cache = VerdictCache(tmp_path / "cache.db")
    cache.put("q", "brave", Verdict(claim="q", status=VerdictStatus.SUPPORTED, confidence=0.9))
    cache.put("q", "exa", Verdict(claim="q", status=VerdictStatus.CONTRADICTED, confidence=0.7))
    a = cache.get("q", "brave")
    b = cache.get("q", "exa")
    assert a is not None and a.status == VerdictStatus.SUPPORTED
    assert b is not None and b.status == VerdictStatus.CONTRADICTED


# ---- Verifier (lexical fallback path) -----------------------------------


def test_verifier_lexical_fallback_high_overlap():
    """When sentence-transformers is absent, the lexical stub gives high
    score to high-overlap snippets."""
    from truthcheck.verifier import _lexical_entail

    snippet = "Türkiye'nin başkenti Ankara'dır ve nüfusu 5 milyondan fazladır."
    claim = "Ankara Türkiye'nin başkentidir"
    score = _lexical_entail(snippet, claim)
    assert score > 0.5


def test_verifier_lexical_fallback_low_overlap():
    from truthcheck.verifier import _lexical_entail

    score = _lexical_entail("apple banana cherry", "Türkiye nüfusu 85 milyon")
    assert score == 0.0


# ---- WebFactChecker (Brave + verifier monkey-patched) -------------------


class _FakeBackend:
    name = "fake"

    def __init__(self, snippets: list[Any]) -> None:
        self.snippets = snippets

    def search(self, query: str, n_results: int = 5) -> list[Any]:
        return self.snippets[:n_results]

    def estimate_cost_usd(self, n_calls: int = 1) -> float:
        return 0.001 * n_calls


def test_web_fact_checker_supports_when_snippet_corroborates(tmp_path):
    from truthcheck import VerdictStatus, WebFactChecker
    from truthcheck.backends import Snippet

    backend = _FakeBackend(
        [
            Snippet(
                url="https://en.wikipedia.org/wiki/Ankara",
                title="Ankara",
                snippet="Ankara Türkiye'nin başkentidir.",
            ),
            Snippet(
                url="https://www.britannica.com/place/Ankara",
                title="Ankara",
                snippet="Ankara is the capital of Turkey.",
            ),
        ]
    )
    fc = WebFactChecker(backend=backend, cache_dir=str(tmp_path / "cache"))
    v = fc.check("Ankara Türkiye'nin başkentidir")
    assert v.status == VerdictStatus.SUPPORTED
    assert len(v.sources) >= 1
    assert v.cost_usd > 0


def test_web_fact_checker_unsupported_when_snippets_irrelevant(tmp_path):
    from truthcheck import VerdictStatus, WebFactChecker
    from truthcheck.backends import Snippet

    backend = _FakeBackend(
        [Snippet(url="https://x.com", title="x", snippet="hello world unrelated")]
    )
    fc = WebFactChecker(backend=backend, cache_dir=str(tmp_path / "cache"))
    v = fc.check("Ankara Türkiye'nin başkentidir")
    assert v.status in {VerdictStatus.UNSUPPORTED, VerdictStatus.INCONCLUSIVE}


def test_web_fact_checker_uses_cache_on_repeat_call(tmp_path):
    """Same claim twice → only one backend hit."""
    from truthcheck import WebFactChecker
    from truthcheck.backends import Snippet

    snip = Snippet(url="https://x.com", title="x", snippet="Ankara başkenttir")
    backend = _FakeBackend([snip])
    n_calls = {"count": 0}

    original_search = backend.search

    def counted_search(query: str, n_results: int = 5):
        n_calls["count"] += 1
        return original_search(query, n_results)

    backend.search = counted_search  # type: ignore[method-assign]

    fc = WebFactChecker(backend=backend, cache_dir=str(tmp_path / "cache"))
    fc.check("Ankara başkenttir")
    fc.check("Ankara başkenttir")  # should hit cache
    # First check might split into 1 atomic claim → 1 search.
    # Second check should hit cache → 0 additional searches.
    assert n_calls["count"] == 1


def test_web_fact_checker_dry_run_estimates_without_search(tmp_path):
    from truthcheck import VerdictStatus, WebFactChecker
    from truthcheck.backends import Snippet

    backend = _FakeBackend([Snippet(url="x", title="x", snippet="x")])
    n_calls = {"count": 0}

    def fail_search(*_a: Any, **_k: Any) -> Any:
        n_calls["count"] += 1
        raise RuntimeError("dry_run should not call search")

    backend.search = fail_search  # type: ignore[method-assign]

    fc = WebFactChecker(backend=backend, cache_dir=str(tmp_path / "cache"), dry_run=True)
    v = fc.check("Türkiye nüfusu 85 milyon")
    assert n_calls["count"] == 0
    assert v.cost_usd > 0
    assert v.status == VerdictStatus.INCONCLUSIVE


def test_estimate_cost_scales_with_atomic_claims(tmp_path):
    """A two-claim sentence costs 2× single-claim."""
    from truthcheck import WebFactChecker
    from truthcheck.backends import Snippet

    backend = _FakeBackend([Snippet(url="x", title="x", snippet="x")])
    fc = WebFactChecker(backend=backend, cache_dir=str(tmp_path / "cache"))
    cost1 = fc.estimate_cost("Tek bir cümle")
    cost2 = fc.estimate_cost("İlk cümle. İkinci cümle.")
    assert cost2 > cost1
