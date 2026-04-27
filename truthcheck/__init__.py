"""truthcheck — open-world fact verification (early draft, no working backend yet)."""
from truthcheck.types import Source, Verdict, VerdictStatus
from truthcheck.web_fact_checker import WebFactChecker

__all__ = ["Source", "Verdict", "VerdictStatus", "WebFactChecker"]
__version__ = "0.0.1"
