"""NLI cross-encoder verifier — does this snippet support the claim?

Same shape as halluguard's NLI path: cross-encoder pairs
(premise=snippet, hypothesis=claim) → entailment score in [0, 1].

Lazy-loaded — when sentence-transformers isn't installed, we fall
back to a "lexical entailment" stub (token overlap). The stub is a
weak signal but lets the rest of the pipeline run for tests / dev
environments without 700MB+ model downloads.
"""
from __future__ import annotations

import importlib.util
import re
from typing import Any


_DEFAULT_MODEL = "cross-encoder/nli-deberta-v3-base"


class NLIVerifier:
    """Score (snippet, claim) pairs for entailment."""

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model: Any = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        if importlib.util.find_spec("sentence_transformers") is None:
            # Stub mode — leave _model as None; entail() uses lexical fallback.
            return
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(self.model_name)

    def entail(self, snippet: str, claim: str) -> float:
        """Return entailment probability in [0, 1]."""
        self._ensure_model()
        if self._model is None:
            return _lexical_entail(snippet, claim)
        scores = self._model.predict([(snippet, claim)], show_progress_bar=False)
        # CrossEncoder NLI: [contradiction, entailment, neutral] for many
        # checkpoints. Normalise to entailment probability.
        import numpy as np

        arr = np.asarray(scores)
        if arr.ndim == 2 and arr.shape[1] == 3:
            entail = float(_softmax(arr[0])[1])
        else:
            # Scalar output → sigmoid
            entail = float(_sigmoid(float(arr.flatten()[0])))
        return max(0.0, min(1.0, entail))


def _lexical_entail(snippet: str, claim: str) -> float:
    """Token-overlap fallback when no NLI model is available.

    This is a weak signal — false-positive prone — but is deterministic
    and lets tests run without network / model downloads.
    """
    snip_tokens = set(re.findall(r"\w+", snippet.lower()))
    claim_tokens = set(re.findall(r"\w+", claim.lower()))
    if not claim_tokens:
        return 0.0
    overlap = len(snip_tokens & claim_tokens) / len(claim_tokens)
    return min(1.0, overlap)


def _softmax(x: Any) -> Any:
    import numpy as np

    e = np.exp(x - np.max(x))
    return e / e.sum()


def _sigmoid(x: float) -> float:
    import math

    return 1.0 / (1.0 + math.exp(-x))
