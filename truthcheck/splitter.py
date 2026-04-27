"""Atomic claim splitting — turn a sentence into verifiable units.

v0.1 ships a minimal regex-based splitter:
  - sentence boundary detection (period / question / exclamation)
  - comma-separated facts within one sentence (Türkiye 85M, 81 il)
  - no NLP, no LLM — deterministic and fast

v0.2 will add either spacy or a small local LLM (Llama 3.2 1B) for
better recall on complex compound claims. The Atakan-gated decision
on the splitting backend is open in the README.
"""
from __future__ import annotations

import re


_SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])")
"""Sentence boundary: end of sentence followed by capital (covers Türkçe)."""

_COMMA_FACT = re.compile(r",\s+(?=\d|[A-ZÇĞİÖŞÜ])")
"""Comma-separated fact within a sentence (e.g. '85 milyon, 81 il')."""


def split_claims(text: str) -> list[str]:
    """Return a list of atomic claim strings extracted from ``text``.

    Order is preserved (claim N appears before claim N+1 in the source).
    Empty / whitespace-only fragments are dropped.
    """
    text = text.strip()
    if not text:
        return []

    # First pass: sentence boundaries.
    sentences = _SENT_END.split(text)
    out: list[str] = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        # Second pass: comma splits within sentences (only when both sides
        # look like factual fragments — number / capital starts).
        parts = _COMMA_FACT.split(sent)
        for p in parts:
            p = p.strip().rstrip(".,;:")
            if p:
                out.append(p)
    return out
