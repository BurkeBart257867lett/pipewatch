"""Alert routing: direct alerts to named channels based on rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus


@dataclass
class RouteRule:
    """A single routing rule mapping conditions to a channel."""
    channel: str
    sources: List[str] = field(default_factory=list)   # empty = match all
    statuses: List[str] = field(default_factory=list)  # empty = match all
    tags: List[str] = field(default_factory=list)      # empty = match all

    def matches(self, alert: Alert) -> bool:
        if self.sources and alert.source not in self.sources:
            return False
        if self.statuses and alert.status.value not in self.statuses:
            return False
        if self.tags:
            alert_tags = set(alert.tags or [])
            if not set(self.tags).issubset(alert_tags):
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "sources": self.sources,
            "statuses": self.statuses,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RouteRule":
        return cls(
            channel=d["channel"],
            sources=d.get("sources", []),
            statuses=d.get("statuses", []),
            tags=d.get("tags", []),
        )


def route_alerts(
    alerts: List[Alert],
    rules: List[RouteRule],
    default_channel: str = "default",
) -> dict[str, List[Alert]]:
    """Return a mapping of channel -> list of alerts routed there."""
    result: dict[str, List[Alert]] = {}
    for alert in alerts:
        matched = False
        for rule in rules:
            if rule.matches(alert):
                result.setdefault(rule.channel, []).append(alert)
                matched = True
                break
        if not matched:
            result.setdefault(default_channel, []).append(alert)
    return result


def format_routing_report(routed: dict[str, List[Alert]]) -> str:
    if not routed:
        return "No alerts to route."
    lines = []
    for channel, alerts in sorted(routed.items()):
        lines.append(f"[{channel}] {len(alerts)} alert(s):")
        for a in alerts:
            lines.append(f"  {a}")
    return "\n".join(lines)
