"""ExaBackend — monkey-patched HTTP tests.

No network, no key required. Verifies request shape, response parsing,
error paths, and that WebFactChecker's default backend is now Exa.
"""
from __future__ import annotations

from typing import Any

import pytest


class _FakeResp:
    def __init__(self, status: int, body: dict[str, Any]) -> None:
        self.status_code = status
        self.ok = 200 <= status < 300
        self._body = body
        self.text = str(body)

    def json(self) -> dict[str, Any]:
        return self._body


def test_exa_backend_requires_api_key(monkeypatch):
    from truthcheck.backends.exa import ExaBackend

    monkeypatch.delenv("EXA_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        ExaBackend()


def test_exa_backend_uses_env_key(monkeypatch):
    from truthcheck.backends.exa import ExaBackend

    monkeypatch.setenv("EXA_API_KEY", "env-key-123")
    b = ExaBackend()
    assert b.api_key == "env-key-123"
    assert b.name == "exa"


def test_exa_backend_explicit_key_overrides_env(monkeypatch):
    from truthcheck.backends.exa import ExaBackend

    monkeypatch.setenv("EXA_API_KEY", "env-key")
    b = ExaBackend(api_key="explicit-key")
    assert b.api_key == "explicit-key"


def test_exa_backend_parses_results_with_highlights(monkeypatch):
    """Snippet.snippet should be the joined highlights when present."""
    from truthcheck.backends.exa import ExaBackend

    captured: dict[str, Any] = {}

    def fake_post(url, headers, json, timeout):  # noqa: A002
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json
        return _FakeResp(
            200,
            {
                "results": [
                    {
                        "id": "https://en.wikipedia.org/wiki/Ankara",
                        "url": "https://en.wikipedia.org/wiki/Ankara",
                        "title": "Ankara",
                        "highlights": [
                            "Ankara is the capital of Turkey",
                            "It has a population of over 5 million",
                        ],
                    },
                    {
                        "url": "https://www.britannica.com/place/Ankara",
                        "title": "Ankara | Encyclopedia",
                        "highlights": ["Ankara, capital of Turkey"],
                    },
                ]
            },
        )

    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    b = ExaBackend(api_key="k")
    snippets = b.search("Ankara capital", n_results=2)

    assert len(snippets) == 2
    assert snippets[0].url == "https://en.wikipedia.org/wiki/Ankara"
    assert "capital of Turkey" in snippets[0].snippet
    assert "5 million" in snippets[0].snippet
    assert captured["body"]["query"] == "Ankara capital"
    assert captured["body"]["numResults"] == 2
    assert captured["body"]["type"] == "auto"
    assert "highlights" in captured["body"]["contents"]
    assert captured["headers"]["x-api-key"] == "k"


def test_exa_backend_falls_back_to_text_when_no_highlights(monkeypatch):
    from truthcheck.backends.exa import ExaBackend

    def fake_post(url, headers, json, timeout):  # noqa: A002
        return _FakeResp(
            200,
            {
                "results": [
                    {"url": "https://x.com", "title": "x", "text": "raw page text"}
                ]
            },
        )

    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    b = ExaBackend(api_key="k")
    snips = b.search("q")
    assert snips[0].snippet == "raw page text"


def test_exa_backend_raises_on_http_error(monkeypatch):
    from truthcheck.backends.exa import ExaBackend

    def fake_post(url, headers, json, timeout):  # noqa: A002
        return _FakeResp(401, {"error": "invalid key"})

    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    b = ExaBackend(api_key="k")
    with pytest.raises(RuntimeError, match="401"):
        b.search("q")


def test_exa_backend_estimate_cost_scales_linearly():
    from truthcheck.backends.exa import ExaBackend

    b = ExaBackend(api_key="k")
    one = b.estimate_cost_usd(1)
    ten = b.estimate_cost_usd(10)
    assert ten == pytest.approx(one * 10)
    assert one > 0


def test_web_fact_checker_default_backend_is_exa(monkeypatch, tmp_path):
    """After Brave's free tier was removed, default must be exa."""
    from truthcheck import WebFactChecker

    monkeypatch.setenv("EXA_API_KEY", "test-key")
    fc = WebFactChecker(cache_dir=str(tmp_path / "cache"))
    assert fc.backend.name == "exa"


def test_web_fact_checker_accepts_brave_string(monkeypatch, tmp_path):
    """Brave still selectable for users with a paid key."""
    from truthcheck import WebFactChecker

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    fc = WebFactChecker(backend="brave", cache_dir=str(tmp_path / "cache"))
    assert fc.backend.name == "brave"


def test_web_fact_checker_rejects_unknown_backend_string(tmp_path):
    from truthcheck import WebFactChecker

    with pytest.raises(ValueError, match="Unknown backend"):
        WebFactChecker(backend="duckduckgo", cache_dir=str(tmp_path / "cache"))
