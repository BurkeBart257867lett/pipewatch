"""Alert deduplication: suppress repeated alerts for the same metric within a time window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from pipewatch.alerts import Alert

DEFAULT_DEDUP_FILE = ".pipewatch_dedup.json"
DEFAULT_WINDOW_SECONDS = 300  # 5 minutes


@dataclass
class DedupState:
    """Tracks the last-seen timestamp for each alert key."""

    window_seconds: int = DEFAULT_WINDOW_SECONDS
    _seen: Dict[str, float] = field(default_factory=dict)

    def _key(self, alert: Alert) -> str:
        return f"{alert.source}::{alert.metric_name}::{alert.status.value}"

    def is_duplicate(self, alert: Alert, now: Optional[float] = None) -> bool:
        """Return True if this alert was already seen within the dedup window."""
        now = now if now is not None else time.time()
        key = self._key(alert)
        last = self._seen.get(key)
        return last is not None and (now - last) < self.window_seconds

    def record(self, alert: Alert, now: Optional[float] = None) -> None:
        """Mark this alert as seen at the given time."""
        now = now if now is not None else time.time()
        self._seen[self._key(alert)] = now

    def to_dict(self) -> dict:
        return {"window_seconds": self.window_seconds, "seen": self._seen}

    @classmethod
    def from_dict(cls, data: dict) -> "DedupState":
        obj = cls(window_seconds=data.get("window_seconds", DEFAULT_WINDOW_SECONDS))
        obj._seen = data.get("seen", {})
        return obj


def _load_state(path: Path) -> DedupState:
    if not path.exists():
        return DedupState()
    try:
        return DedupState.from_dict(json.loads(path.read_text()))
    except (json.JSONDecodeError, KeyError):
        return DedupState()


def _save_state(state: DedupState, path: Path) -> None:
    path.write_text(json.dumps(state.to_dict(), indent=2))


def deduplicate_alerts(
    alerts: List[Alert],
    state_path: str = DEFAULT_DEDUP_FILE,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    now: Optional[float] = None,
) -> List[Alert]:
    """Filter out duplicate alerts seen within the window; persist state to disk."""
    path = Path(state_path)
    state = _load_state(path)
    state.window_seconds = window_seconds

    now = now if now is not None else time.time()
    fresh: List[Alert] = []
    for alert in alerts:
        if not state.is_duplicate(alert, now=now):
            fresh.append(alert)
            state.record(alert, now=now)

    _save_state(state, path)
    return fresh
