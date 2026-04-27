"""Skeleton tests — confirm types + API surface are importable and stable.

These tests intentionally don't exercise check() (it raises). They're
the "is the package wired up" smoke pass — useful for CI before any
backend is implemented.
"""
from __future__ import annotations

import pytest


def test_imports_and_version():
    import truthcheck

    assert truthcheck.__version__ == "0.0.1"
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
    assert v.claim == "x"
    assert v.status == VerdictStatus.SUPPORTED
    assert len(v.sources) == 1
    assert v.sources[0].domain_trust == 1.0  # default


def test_check_raises_not_implemented_until_v0_1():
    from truthcheck import WebFactChecker

    fc = WebFactChecker(backend="brave", api_key="placeholder")
    with pytest.raises(NotImplementedError, match="v0.0"):
        fc.check("anything")


def test_estimate_cost_returns_per_backend_estimate():
    from truthcheck import WebFactChecker

    assert WebFactChecker(backend="brave").estimate_cost("x") == 0.0001
    assert WebFactChecker(backend="exa").estimate_cost("x") == 0.001
    assert WebFactChecker(backend="ddg").estimate_cost("x") == 0.0
    # Unknown backend → conservative non-zero default.
    assert WebFactChecker(backend="custom").estimate_cost("x") == 0.0001
