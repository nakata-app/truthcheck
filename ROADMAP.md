# truthcheck roadmap

> Pre-v0.1. This is the planning document, not a contract. Atakan to
> approve / revise / scrap before any milestone moves to "in progress."

---

## v0.0 — vision (this PR)

- [x] README.md — problem statement + API sketch + design constraints
- [x] ROADMAP.md — this file
- [x] `truthcheck/__init__.py` — public surface stub
- [x] `truthcheck/types.py` — `Verdict`, `Source`, `VerdictStatus` dataclasses
- [x] `truthcheck/web_fact_checker.py` — `WebFactChecker` skeleton (raises NotImplementedError)
- [x] `pyproject.toml` — package metadata, no runtime deps yet

**Exit:** Atakan reviews, opens / closes design questions, decides
whether to spend a v0.1 sprint on the first backend.

---

## v0.1 — first working backend (target: 1 week of focused work)

Open question to lock down before this starts:
- **Backend pick.** Default = ?  Brave / Exa / DuckDuckGo
- **LLM for claim splitting.** Yes / no / behind-a-flag

Ship list (assuming Brave + small-LLM):
- [ ] `BraveBackend` implementing the `SearchBackend` protocol
- [ ] `WebFactChecker.check(claim)` works end-to-end:
  - issue search query against backend
  - fetch top-N snippets (no full-page fetch yet)
  - run NLI cross-encoder (or LLM, TBD) for entailment per snippet
  - aggregate verdict (majority vote across sources)
- [ ] On-disk SQLite cache (claim hash → verdict, configurable TTL)
- [ ] CLI: `truthcheck check "claim text" --backend brave`
- [ ] First benchmark: 50 hand-curated claims, log F1
- [ ] CI matrix (Python 3.10 / 3.11 / 3.12), mypy --strict, ruff,
      coverage upload — same hygiene as the rest of the cluster
- [ ] Honest README "what works" / "what's broken" section

**Exit:** `pip install truthcheck && truthcheck check "..."` returns
a verdict on a real public claim. Numbers committed to
`benchmarks/results_v0_1.json`.

---

## v0.2 — multi-backend + atomic claim splitting (target: 2 weeks)

- [ ] `ExaBackend` — neural search alternative to Brave
- [ ] `DDGScraperBackend` — fallback for users who don't want to
      sign up for an API key (with rate-limit warnings)
- [ ] `AtomicClaimSplitter` — turns one composite sentence into
      multiple atomic verifiable claims:
        in:  "Türkiye nüfusu 85 milyon, 81 il var."
        out: ["Türkiye nüfusu 85 milyon", "Türkiye'de 81 il var"]
      Implementation depends on the v0.1 LLM decision.
- [ ] Per-source trust score (allow-list weights + domain reputation)
- [ ] Composition helper in `claimcheck`:
        `Pipeline.from_corpus_and_web(...)` → halluguard first,
        truthcheck second for the unsupported-by-corpus residue.

**Exit:** README has a side-by-side table (Brave vs Exa vs DDG vs
"all three combined") on the same 50-claim benchmark.

---

## v0.3 — production polish (target: 1 week)

- [ ] PyPI release (`pip install truthcheck`)
- [ ] Cost-budget guards: refuse to spend >X USD/day, configurable
- [ ] Structured audit log (same shape as adaptmem)
- [ ] Recency awareness — flag time-sensitive claims with a TTL
- [ ] Contradiction handling — when sources disagree, surface the
      disagreement instead of forcing a single answer
- [ ] Docker image + healthcheck

**Exit:** `pip install truthcheck` ships, the cluster's
`claimcheck.Pipeline` exposes a `verify_world()` shortcut that
combines halluguard + truthcheck.

---

## Non-goals (until further notice)

- **Replacing halluguard.** They solve different problems.
- **Knowledge graph storage.** Every verdict is fresh from sources.
- **Auto-debunking deepfakes / images.** Text claims only.
- **Truth ranking of sources.** Domain reputation is a heuristic, not
  a science. We surface scores; we don't claim them.
- **Real-time data (stock prices, weather).** That's a different
  category — point users at proper APIs.

---

## What needs Atakan's hand

- **Backend choice + API key budget.** Brave free tier covers
  v0.1 dev; v0.3 production needs a real plan.
- **LLM strategy.** Local (Llama 3.2 1B) vs API (Claude Haiku /
  GPT-4o-mini) vs no-LLM (regex + NLI). Each has different cost,
  latency, and "purity" implications.
- **Repo public-flip decision.** When to push to
  `nakata-app/truthcheck` vs keep private until v0.1 ships.
