"""Dependency tracking between pipeline sources.

Allows declaring that one source depends on another, and checks
whether upstream sources are healthy before flagging downstream failures.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import MetricResult, MetricStatus


@dataclass
class DependencyGraph:
    """Directed graph of source dependencies."""
    edges: Dict[str, List[str]] = field(default_factory=dict)  # source -> [upstream]

    def add_dependency(self, source: str, depends_on: str) -> None:
        """Declare that *source* depends on *depends_on*."""
        self.edges.setdefault(source, [])
        if depends_on not in self.edges[source]:
            self.edges[source].append(depends_on)

    def upstream(self, source: str) -> List[str]:
        """Return direct upstream sources for *source*."""
        return list(self.edges.get(source, []))

    def to_dict(self) -> dict:
        return {"edges": self.edges}

    @classmethod
    def from_dict(cls, data: dict) -> "DependencyGraph":
        g = cls()
        g.edges = {k: list(v) for k, v in data.get("edges", {}).items()}
        return g


@dataclass
class BlockedAlert:
    """Indicates a result was suppressed because an upstream source is unhealthy."""
    source: str
    blocked_by: str
    result: MetricResult

    def __str__(self) -> str:
        return (
            f"[BLOCKED] {self.source}/{self.result.metric.name} "
            f"suppressed — upstream '{self.blocked_by}' is unhealthy"
        )


def _load_raw(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


def _save_raw(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def load_graph(path: str) -> DependencyGraph:
    return DependencyGraph.from_dict(_load_raw(path))


def save_graph(graph: DependencyGraph, path: str) -> None:
    _save_raw(path, graph.to_dict())


def check_dependencies(
    results: List[MetricResult],
    graph: DependencyGraph,
) -> tuple[List[MetricResult], List[BlockedAlert]]:
    """Split *results* into passing-through and blocked.

    A result is blocked when its source has at least one upstream source
    that has an unhealthy result in the current batch.
    """
    unhealthy_sources = {
        r.metric.source
        for r in results
        if r.status in (MetricStatus.WARNING, MetricStatus.CRITICAL)
    }

    clean: List[MetricResult] = []
    blocked: List[BlockedAlert] = []

    for result in results:
        blocker: Optional[str] = None
        for upstream in graph.upstream(result.metric.source):
            if upstream in unhealthy_sources:
                blocker = upstream
                break
        if blocker:
            blocked.append(BlockedAlert(result.metric.source, blocker, result))
        else:
            clean.append(result)

    return clean, blocked


def format_blocked_report(blocked: List[BlockedAlert]) -> str:
    if not blocked:
        return "No results blocked by upstream dependencies."
    lines = ["Blocked results (upstream unhealthy):"]
    for b in blocked:
        lines.append(f"  {b}")
    return "\n".join(lines)
