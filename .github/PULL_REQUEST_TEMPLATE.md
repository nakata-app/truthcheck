## What this changes

<!-- one-paragraph summary; link to a tracking issue if there is one -->

## How it was tested

<!-- pytest output, a manual claim repro, or a search-backend smoke -->

## Checklist

- [ ] `ruff check truthcheck tests` is clean
- [ ] `mypy --strict truthcheck` is clean
- [ ] `pytest -q` passes locally
- [ ] CHANGELOG entry added (under `[Unreleased]`)
- [ ] If this changes the public API (`WebFactChecker.check`,
      `Verdict`, `SearchBackend`): README updated
- [ ] If this adds a search backend: it implements `SearchBackend` and
      ships a fixture-based test
- [ ] If this adds a dependency: it's an `[optional]` extra unless
      truly core
