"""Persistence layer for storing and retrieving metric run history."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_PATH = Path.home() / ".pipewatch" / "history.json"
MAX_HISTORY_ENTRIES = 500


@dataclass
class HistoryEntry:
    timestamp: str
    source: str
    metric_name: str
    value: float
    status: str

    @staticmethod
    def from_dict(data: dict) -> "HistoryEntry":
        return HistoryEntry(
            timestamp=data["timestamp"],
            source=data["source"],
            metric_name=data["metric_name"],
            value=data["value"],
            status=data["status"],
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def append_results(results, path: Path = DEFAULT_HISTORY_PATH) -> None:
    """Append MetricResult objects to the history file."""
    raw = _load_raw(path)
    now = datetime.now(timezone.utc).isoformat()
    for result in results:
        raw.append(
            asdict(
                HistoryEntry(
                    timestamp=now,
                    source=result.metric.source,
                    metric_name=result.metric.name,
                    value=result.value,
                    status=result.status.value,
                )
            )
        )
    # Trim to max size
    if len(raw) > MAX_HISTORY_ENTRIES:
        raw = raw[-MAX_HISTORY_ENTRIES:]
    _save_raw(path, raw)


def load_history(
    path: Path = DEFAULT_HISTORY_PATH,
    source: Optional[str] = None,
    metric_name: Optional[str] = None,
) -> List[HistoryEntry]:
    """Load history entries, optionally filtered by source or metric name."""
    raw = _load_raw(path)
    entries = [HistoryEntry.from_dict(r) for r in raw]
    if source:
        entries = [e for e in entries if e.source == source]
    if metric_name:
        entries = [e for e in entries if e.metric_name == metric_name]
    return entries
