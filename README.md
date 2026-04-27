# truthcheck

**Open-world fact verification for AI claims, the web-search complement to [`halluguard`](https://github.com/nakata-app/halluguard).**

> Status: **v0.1, working.** Pipeline ships: Exa search backend, NLI verifier
> (lexical fallback when sentence-transformers not installed), SQLite cache,
> atomic claim splitter. Sibling to `adaptmem` + `halluguard` + `claimcheck`.

---

## The problem this solves

`halluguard` answers: *"Is this claim supported by **the documents I gave you**?"*

That's enough when you control the corpus (your shop's catalog, your
company's internal docs, your codebase). It is **not** enough when:

- An LLM cites a figure ("Türkiye nüfusu 85 milyon").
- An LLM dates an event ("Bitcoin halving was in May 2024").
- An LLM names a person ("Alice Novak is the lead developer of Project X").
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
    backend="exa",                       # default; "brave" also supported
    api_key=os.environ["EXA_API_KEY"],
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

## v0.1 decisions (closed)

- **Default backend:** Exa (Brave's free tier was removed)
- **Splitter:** regex-based, deterministic, spacy/LLM in v0.2
- **Verifier:** NLI cross-encoder; lexical fallback when sentence-transformers absent
- **Cache:** SQLite under `~/.cache/truthcheck`
- **Contradiction:** INCONCLUSIVE + all sources surfaced
- **Recency:** `as_of` timestamp stamped on every verdict

## Open for v0.2

- Turkish / multilingual NLI model
- spacy or small LLM for compound claim splitting
- DDG / SearXNG backend (no API key)
- Redis cache backend

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

MIT

## Install

```bash
pip install "truthcheck[brave]"   # Brave backend
pip install "truthcheck[nli]"     # NLI verifier (sentence-transformers)
```

Set `EXA_API_KEY` or `BRAVE_API_KEY` env var before use.

---

**This is a draft.** Atakan to review, sharpen the open questions, and
decide whether to push public + commit to the v0.1 milestone.
 
 
 
 
