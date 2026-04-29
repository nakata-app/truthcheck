# Changelog

All notable changes to **truthcheck** are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versions follow
[SemVer](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-04-29

Governance + CI hygiene release. No public-API change. Re-publish under
the same `nakata-truthcheck` distribution name on PyPI.

### Added
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` (this file).
- `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/` (bug
  report + feature request).

### Changed
- `pyproject.toml` mypy override now ignores missing stubs for `numpy`
  in addition to `requests` / `sentence_transformers`. Prevents a
  spurious `import-not-found` on the lazy `import numpy as np` inside
  `verifier.py` when CI runs without the `[nli]` extra.
- `[dev]` extras now include `pytest-cov>=4.1` so the CI workflow's
  `pytest --cov=truthcheck` step does not fail with
  `unrecognized arguments: --cov=`.

## [0.1.0] - 2026-04-29

First working release. The full pipeline ships: open-web search,
evidence retrieval, NLI verification, atomic claim splitting, and a
SQLite-backed result cache.

### Added
- `truthcheck.WebFactChecker`, high-level entry point. Takes a claim
  string, returns a `Verdict` with verdict label, confidence, and the
  evidence the verdict was derived from. Never raises on a missing
  backend or empty result; populates `Verdict.error` instead.
- `truthcheck.backends.ExaBackend`, Exa search API adapter. Reads
  `EXA_API_KEY` from the environment.
- `truthcheck.backends.SearchBackend` protocol so callers can plug in
  alternate providers (Brave, Google CSE, internal search) without
  patching the core.
- NLI-based verifier with a deterministic lexical fallback when
  `sentence-transformers` is not installed. The fallback is intentionally
  simple, better than nothing, transparent, no surprise dependencies.
- Atomic claim splitter, accepts compound claims and yields one
  decision per atom.
- SQLite-backed `Cache` keyed by claim + backend + verifier, with TTL
  and lookup-only / read-write modes.

### Internals
- 18 unit tests (mocked backends + lexical-fallback verifier),
  mypy `--strict` clean, ruff clean.
- No mandatory runtime dependencies beyond `requests`. Heavy deps
  (`sentence-transformers`, `torch`) are `[ml]` optional extras.
- PyPI distribution name: `nakata-truthcheck` (the bare `truthcheck`
  slug was taken). Import path stays `truthcheck`.

[0.1.1]: https://github.com/nakata-app/truthcheck/releases/tag/v0.1.1
[0.1.0]: https://github.com/nakata-app/truthcheck/releases/tag/v0.1.0
