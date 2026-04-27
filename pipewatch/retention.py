"""Retention policy: prune old history entries beyond a configurable age or count."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pipewatch.history import HistoryEntry, _load_raw, _save_raw


@dataclass
class RetentionPolicy:
    max_age_days: Optional[int] = None   # drop entries older than this
    max_entries: Optional[int] = None    # keep only the N most recent entries

    def is_valid(self) -> bool:
        return self.max_age_days is not None or self.max_entries is not None


@dataclass
class PruneResult:
    removed: int
    kept: int

    def __str__(self) -> str:  # pragma: no cover
        return f"Pruned {self.removed} entr{'y' if self.removed == 1 else 'ies'}, {self.kept} remaining."


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string into an aware datetime."""
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def prune_history(history_path: str, policy: RetentionPolicy) -> PruneResult:
    """Apply *policy* to the history file at *history_path* in-place.

    Returns a :class:`PruneResult` describing how many entries were removed.
    """
    raw: List[dict] = _load_raw(history_path)
    original_count = len(raw)

    if policy.max_age_days is not None:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=policy.max_age_days)
        raw = [e for e in raw if _parse_ts(e.get("timestamp", "1970-01-01")) >= cutoff]

    if policy.max_entries is not None and len(raw) > policy.max_entries:
        raw = raw[-policy.max_entries:]

    _save_raw(history_path, raw)
    removed = original_count - len(raw)
    return PruneResult(removed=removed, kept=len(raw))


def format_prune_result(result: PruneResult) -> str:
    return str(result)
