# Contributing to truthcheck

Thanks for considering a contribution. The repo is small enough that the
review pipeline is short, keep changes focused, the bar is "honest
verdicts + clear tradeoffs."

## Quickstart for a local dev loop

```bash
git clone https://github.com/nakata-app/truthcheck.git
cd truthcheck
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

To exercise the live web-search backend you'll need an Exa API key:

```bash
export EXA_API_KEY=...
```

Without the key the live tests are skipped; the rest of the suite uses
fixtures and runs offline.

## What we run before every commit

```bash
ruff check truthcheck tests             # lint
mypy --strict truthcheck                # type check
pytest -q                               # unit tests
```

CI runs the same three on Python 3.10 / 3.11 / 3.12. A PR that doesn't
pass them locally won't pass CI either.

## What lands easily

- Bug fixes with a regression test that fails before / passes after.
- New search backends behind the existing
  `truthcheck.backends.SearchBackend` protocol. Vendor-neutrality is a
  feature; please don't bake an Exa-only assumption deeper into the
  pipeline.
- New verifier strategies (richer NLI, stronger claim splitting, better
  evidence ranking) gated behind feature flags so the deterministic
  default keeps shipping.
- Cache improvements (TTL, eviction, sharding). The SQLite cache is
  intentionally simple; harder-edge backends (Redis, Postgres) are
  welcome as opt-in extras.

## What needs a discussion first

- Anything that changes the public API surface
  (`WebFactChecker.check`, the `Verdict` shape, the
  `SearchBackend` protocol).
- Adding an LLM into the inference path. truthcheck is intentionally
  LLM-free at decision time; an LLM can help with claim splitting in
  an opt-in mode but must never silently grade evidence.
- New required dependencies. We try hard to keep the core install
  small; new heavy dependencies should be `[optional]` extras.

## Style

- Match the existing code. Type hints on public surfaces; no
  speculative abstractions; comments only for non-obvious WHY.
- One commit per logical change. Squash if you accumulate "fix
  comments" commits.
- Commit messages: imperative mood, short subject ("add Brave
  backend"), longer body if the change is non-trivial.

## Reporting bugs

GitHub Issues. Include:
- Python version + OS.
- The minimum reproduction (one claim + the expected verdict is
  enough).
- What you expected vs what you got.
- Whether you ran with a live backend or against fixtures.

## Reporting security issues

See [`SECURITY.md`](SECURITY.md). Don't open a public issue for an
unpatched vulnerability.
