"""Snapshot module: capture and compare pipeline metric states at a point in time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.metrics import MetricResult, MetricStatus


@dataclass
class Snapshot:
    """A named, timestamped capture of MetricResults."""

    name: str
    captured_at: str
    results: List[MetricResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "captured_at": self.captured_at,
            "results": [
                {
                    "source": r.metric.source,
                    "name": r.metric.name,
                    "value": r.value,
                    "status": r.status.value,
                    "tags": r.metric.tags,
                }
                for r in self.results
            ],
        }

    @staticmethod
    def from_dict(d: dict) -> "Snapshot":
        from pipewatch.metrics import Metric

        results = [
            MetricResult(
                metric=Metric(
                    source=r["source"],
                    name=r["name"],
                    tags=r.get("tags", []),
                ),
                value=r["value"],
                status=MetricStatus(r["status"]),
            )
            for r in d.get("results", [])
        ]
        return Snapshot(name=d["name"], captured_at=d["captured_at"], results=results)


def _snapshot_path(store_dir: str, name: str) -> str:
    safe = name.replace(" ", "_")
    return os.path.join(store_dir, f"{safe}.json")


def save_snapshot(
    results: List[MetricResult],
    name: str,
    store_dir: str = ".pipewatch/snapshots",
) -> Snapshot:
    """Persist a snapshot to disk and return it."""
    os.makedirs(store_dir, exist_ok=True)
    snap = Snapshot(
        name=name,
        captured_at=datetime.now(timezone.utc).isoformat(),
        results=results,
    )
    path = _snapshot_path(store_dir, name)
    with open(path, "w") as fh:
        json.dump(snap.to_dict(), fh, indent=2)
    return snap


def load_snapshot(name: str, store_dir: str = ".pipewatch/snapshots") -> Optional[Snapshot]:
    """Load a previously saved snapshot by name, or None if not found."""
    path = _snapshot_path(store_dir, name)
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return Snapshot.from_dict(json.load(fh))


def list_snapshots(store_dir: str = ".pipewatch/snapshots") -> List[str]:
    """Return names of all saved snapshots."""
    if not os.path.isdir(store_dir):
        return []
    return [
        os.path.splitext(f)[0].replace("_", " ")
        for f in sorted(os.listdir(store_dir))
        if f.endswith(".json")
    ]


@dataclass
class SnapshotDiff:
    """Difference between two snapshots."""

    added: List[MetricResult] = field(default_factory=list)
    removed: List[MetricResult] = field(default_factory=list)
    changed: List[tuple] = field(default_factory=list)  # (before, after)

    def __str__(self) -> str:
        lines = []
        for r in self.added:
            lines.append(f"  + {r.metric.source}/{r.metric.name} = {r.value} [{r.status.value}]")
        for r in self.removed:
            lines.append(f"  - {r.metric.source}/{r.metric.name} (removed)")
        for before, after in self.changed:
            lines.append(
                f"  ~ {before.metric.source}/{before.metric.name}: "
                f"{before.value} [{before.status.value}] -> "
                f"{after.value} [{after.status.value}]"
            )
        return "\n".join(lines) if lines else "  (no differences)"


def diff_snapshots(before: Snapshot, after: Snapshot) -> SnapshotDiff:
    """Compute the diff between two snapshots."""
    before_map: Dict[tuple, MetricResult] = {
        (r.metric.source, r.metric.name): r for r in before.results
    }
    after_map: Dict[tuple, MetricResult] = {
        (r.metric.source, r.metric.name): r for r in after.results
    }

    added = [after_map[k] for k in after_map if k not in before_map]
    removed = [before_map[k] for k in before_map if k not in after_map]
    changed = [
        (before_map[k], after_map[k])
        for k in before_map
        if k in after_map
        and (before_map[k].value != after_map[k].value or before_map[k].status != after_map[k].status)
    ]
    return SnapshotDiff(added=added, removed=removed, changed=changed)
