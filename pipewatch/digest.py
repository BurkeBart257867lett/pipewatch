"""Periodic digest report: summarise metric health across all sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from pipewatch.metrics import MetricResult, MetricStatus


@dataclass
class DigestSummary:
    total: int = 0
    ok: int = 0
    warning: int = 0
    critical: int = 0
    by_source: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def __str__(self) -> str:  # noqa: D105
        lines = [
            "=== Pipewatch Digest ===",
            f"Total metrics : {self.total}",
            f"  OK          : {self.ok}",
            f"  Warning     : {self.warning}",
            f"  Critical    : {self.critical}",
        ]
        if self.by_source:
            lines.append("\nBy source:")
            for src, counts in sorted(self.by_source.items()):
                ok = counts.get("ok", 0)
                warn = counts.get("warning", 0)
                crit = counts.get("critical", 0)
                lines.append(f"  {src}: ok={ok} warn={warn} crit={crit}")
        return "\n".join(lines)


def build_digest(results: List[MetricResult]) -> DigestSummary:
    """Aggregate a list of MetricResults into a DigestSummary."""
    summary = DigestSummary()
    for result in results:
        summary.total += 1
        source = result.source
        if source not in summary.by_source:
            summary.by_source[source] = {"ok": 0, "warning": 0, "critical": 0}

        status = result.status
        if status == MetricStatus.OK:
            summary.ok += 1
            summary.by_source[source]["ok"] += 1
        elif status == MetricStatus.WARNING:
            summary.warning += 1
            summary.by_source[source]["warning"] += 1
        elif status == MetricStatus.CRITICAL:
            summary.critical += 1
            summary.by_source[source]["critical"] += 1

    return summary


def format_digest(results: List[MetricResult]) -> str:
    """Return a formatted digest string for the given results."""
    return str(build_digest(results))
