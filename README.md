# truthcheck

**Open-world fact verification for AI claims, the web-search complement to [`halluguard`](https://github.com/nakata-app/halluguard).**

> Status: **early draft / vision document.** No working implementation yet. The
> sibling cluster (`adaptmem` + `halluguard` + `claimcheck`) ships today and
> handles the closed-world case. Truthcheck is the open-world counterpart and
> is intentionally a separate package so it doesn't compromise the
> "no LLM, no internet" positioning of halluguard.

---

## The problem this solves

`halluguard` answers: *"Is this claim supported by **the documents I gave you**?"*

That's enough when you control the corpus (your shop's catalog, your
company's internal docs, your codebase). It is **not** enough when:

- An LLM cites a figure ("Türkiye nüfusu 85 milyon").
- An LLM dates an event ("Bitcoin halving was in May 2024").
- An LLM names a person ("Ben Sigman is the lead developer of MemPalace").
- An LLM repeats a recent news fact ("OpenAI released o4-mini in March 2026").

Halluguard can't answer because the **ground truth** lives on the open web,
not in the user's corpus. That's `truthcheck`'s job.

## Design constraints

1. **Stay composable.** Truthcheck is a sibling, not a replacement.
   - `halluguard.Guard.check(answer)` → corpus-grounded verdict
   - `truthcheck.WebFactChecker.check(claim)` → open-web verdict
   - Caller decides which to invoke (or both, in series).
2. **Never silently dilute halluguard's positioning.** Halluguard says
   "no LLM, no internet, deterministic." Truthcheck explicitly says
   "yes LLM (probably), yes internet, probabilistic." Honest naming.
3. **Backend-agnostic.** Brave Search, Exa, Bing, DuckDuckGo, your
   internal corporate Confluence + Notion, anything that returns
   ranked snippets should plug in.
4. **Cost-aware.** Web search APIs cost money. Truthcheck must
   - tell the caller a USD estimate per claim before issuing requests
   - cache aggressively (claim text → result, TTL configurable)
   - support `dry_run=True` to preview without API spend.

## Sketch of the API

```python
from truthcheck import WebFactChecker

checker = WebFactChecker(
    backend="brave",                    # or "exa", "bing", "ddg"
    api_key=os.environ["BRAVE_API_KEY"],
    trusted_domains=["wikipedia.org", "*.gov", "*.edu"],
    cache_dir="~/.cache/truthcheck",
)

verdict = checker.check(
    claim="Türkiye nüfusu 85 milyon",
    n_sources=5,
)
# Verdict {
#   status: SUPPORTED | UNSUPPORTED | CONTRADICTED | INCONCLUSIVE,
#   confidence: 0.0, 1.0,
#   sources: [
#     Source(url="https://www.worldometers.info/...", snippet="...", score=0.91),
#     Source(url="https://en.wikipedia.org/wiki/Demographics_of_Turkey", ...),
#     ...
#   ],
#   atomic_claims: ["country: Türkiye", "metric: population", "value: 85 million"],
#   cost_usd: 0.0007,
#   cache_hit: False,
# }
```

## Open design questions (need decisions before v0.1)

1. **Default backend.** Brave (free 2k/mo), Exa (1k/mo), DuckDuckGo (no API,
   needs scraping). Pick one default; let the rest be opt-in.
2. **Atomic claim splitting.** "Türkiye nüfusu 85 milyon, 81 il" is two
   claims. Split with regex? Spacy? Small LLM (Llama 3.2 1B locally)?
   Each option has a different "no LLM" violation tier.
3. **Trusted-domain policy.** Allow-list only (strict, narrow), allow-list
   weighted (loose, flexible), or domain-reputation score (Wikipedia
   high, random blog low)?
4. **Recency awareness.** Some claims are time-sensitive ("Bitcoin price
   today"). Should truthcheck refuse those, mark them with a low
   confidence ceiling, or stamp a "as-of date" on the verdict?
5. **Contradiction handling.** Three sources say 85 million, two say
   84 million. Majority wins? Highest-trust wins? Both reported?
6. **API surface for caching.** Disk only? Redis? Plug-in storage? Default
   to SQLite under XDG cache.
7. **LLM optionality.** Truthcheck almost certainly needs an LLM for
   atomic claim splitting and source-snippet entailment. Make it
   pluggable so a sufficiently advanced regex / NLI pipeline could
   substitute. Document the tradeoff explicitly in the README.

## Composition with the cluster

```
                       answer + corpus → halluguard.Guard.check()
                                                │
                                                ▼
                                    SUPPORTED?  yes ─→ trust=high, done
                                       │
                                       no (claim isn't in corpus)
                                       │
                                       ▼
                              answer claims → truthcheck.WebFactChecker.check()
                                                │
                                                ▼
                                       open-web verdict
```

Bigger picture: cluster gives the consumer a **"belge → halluguard, dünya
→ truthcheck"** pipeline so closed-world and open-world claims can both be
verified through one call site (a future helper in `claimcheck`).

## What this repo is NOT

- **Not a replacement for halluguard.** Halluguard handles the case
  where you have a corpus. Don't use truthcheck where halluguard fits.
- **Not a search engine.** It's a verification layer that uses search
  engines as a substrate. Bring your own backend.
- **Not a fact-database.** It doesn't ship knowledge graphs. Every
  verdict is computed at request time against live sources.
- **Not a guarantee.** Open-world fact-checking is an active research
  area; FEVER state-of-the-art is around 75% F1. Truthcheck reports
  confidence, never asserts truth.

## License

MIT (planned, not yet committed, repo is pre-v0.1).

## Status

Pre-v0.1. This README is the design doc. No code beyond stubs yet.
Read [`ROADMAP.md`](ROADMAP.md) for the milestone breakdown.

---

**This is a draft.** Atakan to review, sharpen the open questions, and
decide whether to push public + commit to the v0.1 milestone.
 
