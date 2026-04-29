# Security policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive
findings. Instead, email the maintainer at
**hey@nakata.app** with:

- A description of the issue.
- Steps to reproduce (a minimal repro is enough).
- The version / commit you tested against.
- Optionally, your proposed fix.

We aim to acknowledge a report within 72 hours and to ship a fix in
the next minor release where applicable.

## Scope

The Python package itself is the in-scope surface: `WebFactChecker`,
the search-backend protocol, the NLI verifier, and the SQLite cache.

Out of scope:
- Bugs in third-party search APIs we call (Exa, Brave, etc.). Report
  those upstream.
- Bugs in `sentence-transformers` / `transformers` / `torch`. Report
  those upstream.
- Performance issues without a security impact (file regular issues
  instead).

## Threat model

truthcheck reads claims from the caller, queries third-party search
APIs, parses their JSON, and returns a verdict. It does not bind
network sockets and does not execute remote payloads.

**Untrusted input:** the claim string and the documents returned by
search backends. We never `eval`, `exec`, or template untrusted text
into shell commands. Callers should still treat the verdict's
evidence snippets as untrusted markdown / HTML when rendering them in
a UI.

**Trusted input:** the search-backend API key and the local cache
path. truthcheck does not log API keys; if you add a new backend,
keep it that way.

## API key handling

- Keys are read from environment variables (`EXA_API_KEY`, etc.).
- We never copy them into the cache, into logs, or into the verdict.
- If you add a backend, follow the same convention; do not write keys
  to disk.
