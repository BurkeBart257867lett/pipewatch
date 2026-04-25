"""Aggregation utilities for grouping and summarizing MetricResults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import MetricResult, MetricStatus


@dataclass
class AggregatedGroup:
    """Summary statistics for a group of MetricResults."""

    group_key: str
    total: int = 0
    ok_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    values: List[float] = field(default_factory=list)

    @property
    def health_ratio(self) -> float:
        """Fraction of results that are OK (0.0 – 1.0)."""
        if self.total == 0:
            return 1.0
        return self.ok_count / self.total

    @property
    def avg_value(self) -> Optional[float]:
        """Mean of all numeric values in the group, or None if empty."""
        if not self.values:
            return None
        return sum(self.values) / len(self.values)

    @property
    def max_value(self) -> Optional[float]:
        return max(self.values) if self.values else None

    @property
    def min_value(self) -> Optional[float]:
        return min(self.values) if self.values else None

    def __str__(self) -> str:
        avg = f"{self.avg_value:.4g}" if self.avg_value is not None else "n/a"
        return (
            f"[{self.group_key}] total={self.total} "
            f"ok={self.ok_count} warn={self.warning_count} crit={self.critical_count} "
            f"avg={avg} health={self.health_ratio:.0%}"
        )


def aggregate_by_source(results: List[MetricResult]) -> Dict[str, AggregatedGroup]:
    """Group results by their source name."""
    return _aggregate(results, key_fn=lambda r: r.source)


def aggregate_by_metric(results: List[MetricResult]) -> Dict[str, AggregatedGroup]:
    """Group results by their metric name."""
    return _aggregate(results, key_fn=lambda r: r.metric.name)


def aggregate_by_tag(results: List[MetricResult], tag: str) -> Dict[str, AggregatedGroup]:
    """Group results by the value of a specific tag key."""
    def _key(r: MetricResult) -> str:
        tags: Dict[str, str] = getattr(r.metric, "tags", {}) or {}
        return tags.get(tag, "<untagged>")

    return _aggregate(results, key_fn=_key)


def _aggregate(results: List[MetricResult], *, key_fn) -> Dict[str, AggregatedGroup]:
    groups: Dict[str, AggregatedGroup] = {}
    for result in results:
        key = key_fn(result)
        if key not in groups:
            groups[key] = AggregatedGroup(group_key=key)
        grp = groups[key]
        grp.total += 1
        if result.status == MetricStatus.OK:
            grp.ok_count += 1
        elif result.status == MetricStatus.WARNING:
            grp.warning_count += 1
        elif result.status == MetricStatus.CRITICAL:
            grp.critical_count += 1
        if result.value is not None:
            grp.values.append(result.value)
    return groups


def format_aggregation_report(groups: Dict[str, AggregatedGroup]) -> str:
    """Return a human-readable report string for a dict of AggregatedGroups.

    Groups are sorted alphabetically by their key so the output is stable
    across runs regardless of insertion order.

    Args:
        groups: Mapping of group key to AggregatedGroup, as returned by any
                of the ``aggregate_by_*`` helpers.

    Returns:
        A newline-separated string with one line per group, or a placeholder
        message when *groups* is empty.
    """
    if not groups:
        return "No aggregation data available."
    lines = [str(grp) for _, grp in sorted(groups.items())]
    return "\n".join(lines)
