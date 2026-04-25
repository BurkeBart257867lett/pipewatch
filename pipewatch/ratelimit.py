"""Rate limiting for alert channels — caps how many alerts can fire per channel within a time window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_PATH = Path(".pipewatch_ratelimit.json")


@dataclass
class ChannelRateState:
    channel: str
    window_seconds: int
    max_alerts: int
    timestamps: list = field(default_factory=list)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def is_allowed(self, now: Optional[float] = None) -> bool:
        now = now or time.time()
        self._prune(now)
        return len(self.timestamps) < self.max_alerts

    def record(self, now: Optional[float] = None) -> None:
        now = now or time.time()
        self._prune(now)
        self.timestamps.append(now)

    def remaining(self, now: Optional[float] = None) -> int:
        now = now or time.time()
        self._prune(now)
        return max(0, self.max_alerts - len(self.timestamps))

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "window_seconds": self.window_seconds,
            "max_alerts": self.max_alerts,
            "timestamps": self.timestamps,
        }

    @staticmethod
    def from_dict(d: dict) -> "ChannelRateState":
        return ChannelRateState(
            channel=d["channel"],
            window_seconds=d["window_seconds"],
            max_alerts=d["max_alerts"],
            timestamps=d.get("timestamps", []),
        )


def _load(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(path: Path, data: Dict[str, dict]) -> None:
    path.write_text(json.dumps(data, indent=2))


def get_state(channel: str, window_seconds: int, max_alerts: int,
              path: Path = _DEFAULT_PATH) -> ChannelRateState:
    raw = _load(path)
    if channel in raw:
        return ChannelRateState.from_dict(raw[channel])
    return ChannelRateState(channel=channel, window_seconds=window_seconds, max_alerts=max_alerts)


def save_state(state: ChannelRateState, path: Path = _DEFAULT_PATH) -> None:
    raw = _load(path)
    raw[state.channel] = state.to_dict()
    _save(path, raw)


def clear_channel(channel: str, path: Path = _DEFAULT_PATH) -> None:
    raw = _load(path)
    raw.pop(channel, None)
    _save(path, raw)
