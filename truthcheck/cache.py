"""SQLite-backed verdict cache.

Web search costs money + adds latency. Same claim asked twice should
hit cache, not API. TTL-aware so stale verdicts roll over.

Key: SHA256(claim + backend_name) — collision-resistant, deterministic.
Value: pickled Verdict + timestamp.
"""
from __future__ import annotations

import hashlib
import pickle
import sqlite3
import time
from pathlib import Path

from truthcheck.types import Verdict


_SCHEMA = """
CREATE TABLE IF NOT EXISTS verdicts (
    cache_key   TEXT PRIMARY KEY,
    payload     BLOB NOT NULL,
    written_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_written_at ON verdicts(written_at);
"""


class VerdictCache:
    """SQLite key-value store for cached Verdict objects."""

    def __init__(self, db_path: str | Path, ttl_seconds: int = 7 * 24 * 3600) -> None:
        """Open / create the cache file.

        Args:
            db_path: where to store the SQLite file (created if missing).
            ttl_seconds: how long a cached verdict stays valid. Default 7d.
        """
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.path), isolation_level=None, check_same_thread=False
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def _key(claim: str, backend_name: str) -> str:
        h = hashlib.sha256()
        h.update(backend_name.encode())
        h.update(b"\x00")
        h.update(claim.encode())
        return h.hexdigest()

    def get(self, claim: str, backend_name: str) -> Verdict | None:
        """Return the cached verdict if fresh, else None."""
        row = self._conn.execute(
            "SELECT payload, written_at FROM verdicts WHERE cache_key = ?",
            (self._key(claim, backend_name),),
        ).fetchone()
        if row is None:
            return None
        payload, written_at = row
        if time.time() - written_at > self.ttl_seconds:
            return None  # expired; treat as miss
        verdict: Verdict = pickle.loads(payload)
        return verdict

    def put(self, claim: str, backend_name: str, verdict: Verdict) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO verdicts (cache_key, payload, written_at) VALUES (?, ?, ?)",
                (
                    self._key(claim, backend_name),
                    pickle.dumps(verdict),
                    time.time(),
                ),
            )

    def close(self) -> None:
        self._conn.close()
