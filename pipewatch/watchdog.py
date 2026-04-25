"""Watchdog: detect stale sources that have not reported metrics recently."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.history import HistoryEntry


@dataclass
class StalenessAlert:
    source: str
    last_seen: Optional[datetime]
    stale_seconds: float

    def __str__(self) -> str:
        if self.last_seen is None:
            return f"[STALE] {self.source}: never reported"
        age = int(self.stale_seconds)
        return f"[STALE] {self.source}: last seen {self.last_seen.isoformat()} ({age}s ago)"


def _latest_timestamp(entries: List[HistoryEntry], source: str) -> Optional[datetime]:
    """Return the most recent timestamp for *source* across all history entries."""
    latest: Optional[datetime] = None
    for entry in entries:
        for result in entry.results:
            if result.metric.source != source:
                continue
            ts = entry.timestamp
            if latest is None or ts > latest:
                latest = ts
    return latest


def check_staleness(
    entries: List[HistoryEntry],
    sources: List[str],
    threshold_seconds: float = 3600.0,
    now: Optional[datetime] = None,
) -> List[StalenessAlert]:
    """Return a :class:`StalenessAlert` for every source that has not reported
    within *threshold_seconds*.

    Parameters
    ----------
    entries:
        Full history as returned by :func:`pipewatch.history.load_history`.
    sources:
        Canonical list of expected source names (from config).
    threshold_seconds:
        How many seconds of silence before a source is considered stale.
    now:
        Reference time (defaults to UTC now).  Useful for testing.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    alerts: List[StalenessAlert] = []
    for source in sources:
        last_seen = _latest_timestamp(entries, source)
        if last_seen is None:
            alerts.append(StalenessAlert(source=source, last_seen=None, stale_seconds=float("inf")))
            continue
        age = (now - last_seen).total_seconds()
        if age > threshold_seconds:
            alerts.append(StalenessAlert(source=source, last_seen=last_seen, stale_seconds=age))
    return alerts


def format_staleness_report(alerts: List[StalenessAlert]) -> str:
    """Return a human-readable staleness report string."""
    if not alerts:
        return "All sources reporting within threshold."
    lines = ["Stale sources detected:"] + [f"  {a}" for a in alerts]
    return "\n".join(lines)
