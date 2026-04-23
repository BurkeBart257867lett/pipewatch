"""Tag-based filtering for metrics and results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from pipewatch.metrics import MetricResult


@dataclass
class TagFilter:
    """Holds a set of required tags used to filter MetricResults."""

    tags: set[str] = field(default_factory=set)

    @classmethod
    def from_list(cls, tags: Iterable[str]) -> "TagFilter":
        return cls(tags=set(tags))

    def matches(self, result: MetricResult) -> bool:
        """Return True if *all* required tags are present on the result's metric."""
        if not self.tags:
            return True
        metric_tags: set[str] = set(getattr(result.metric, "tags", None) or [])
        return self.tags.issubset(metric_tags)

    def __bool__(self) -> bool:
        return bool(self.tags)


def filter_results(
    results: list[MetricResult],
    tags: Iterable[str] | None = None,
) -> list[MetricResult]:
    """Return only those results whose metric carries *all* of the given tags.

    If *tags* is empty or None every result is returned unchanged.
    """
    if not tags:
        return list(results)
    tf = TagFilter.from_list(tags)
    return [r for r in results if tf.matches(r)]


def collect_all_tags(results: list[MetricResult]) -> list[str]:
    """Return a sorted, deduplicated list of every tag found across *results*."""
    seen: set[str] = set()
    for r in results:
        seen.update(getattr(r.metric, "tags", None) or [])
    return sorted(seen)
