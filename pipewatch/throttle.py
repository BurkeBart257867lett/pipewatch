"""Alert throttling: suppress repeated alerts within a cooldown window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_THROTTLE_FILE = ".pipewatch_throttle.json"


@dataclass
class ThrottleState:
    """Tracks the last alert time for a given key."""

    last_fired: Dict[str, float] = field(default_factory=dict)

    def should_fire(self, key: str, cooldown_seconds: float) -> bool:
        """Return True if enough time has passed since the last alert for key."""
        now = time.time()
        last = self.last_fired.get(key)
        if last is None:
            return True
        return (now - last) >= cooldown_seconds

    def record(self, key: str) -> None:
        """Record that an alert for key fired right now."""
        self.last_fired[key] = time.time()

    def to_dict(self) -> dict:
        return {"last_fired": self.last_fired}

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleState":
        return cls(last_fired=data.get("last_fired", {}))


def _load_state(path: Path) -> ThrottleState:
    if not path.exists():
        return ThrottleState()
    try:
        data = json.loads(path.read_text())
        return ThrottleState.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return ThrottleState()


def _save_state(state: ThrottleState, path: Path) -> None:
    path.write_text(json.dumps(state.to_dict(), indent=2))


def filter_throttled(
    alert_keys: list[str],
    cooldown_seconds: float,
    throttle_file: Optional[str] = None,
) -> list[str]:
    """Return only those alert keys that are not throttled.

    Side-effect: records fired alerts and persists state.
    """
    path = Path(throttle_file or DEFAULT_THROTTLE_FILE)
    state = _load_state(path)
    allowed = []
    for key in alert_keys:
        if state.should_fire(key, cooldown_seconds):
            state.record(key)
            allowed.append(key)
    _save_state(state, path)
    return allowed
