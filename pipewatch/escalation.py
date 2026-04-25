"""Escalation policy: re-alert when a metric stays unhealthy for N consecutive runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os

from pipewatch.metrics import MetricResult, MetricStatus


@dataclass
class EscalationState:
    """Tracks how many consecutive unhealthy runs a (source, metric) pair has had."""
    source: str
    metric: str
    consecutive_unhealthy: int = 0
    last_status: str = MetricStatus.OK

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "metric": self.metric,
            "consecutive_unhealthy": self.consecutive_unhealthy,
            "last_status": self.last_status,
        }

    @staticmethod
    def from_dict(d: dict) -> "EscalationState":
        return EscalationState(
            source=d["source"],
            metric=d["metric"],
            consecutive_unhealthy=d.get("consecutive_unhealthy", 0),
            last_status=d.get("last_status", MetricStatus.OK),
        )


@dataclass
class EscalationAlert:
    source: str
    metric: str
    consecutive_count: int
    status: str

    def __str__(self) -> str:
        return (
            f"[ESCALATION] {self.source}/{self.metric} has been {self.status} "
            f"for {self.consecutive_count} consecutive run(s)"
        )


def _load_state(path: str) -> Dict[str, EscalationState]:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {k: EscalationState.from_dict(v) for k, v in raw.items()}


def _save_state(path: str, state: Dict[str, EscalationState]) -> None:
    with open(path, "w") as f:
        json.dump({k: v.to_dict() for k, v in state.items()}, f, indent=2)


def _key(source: str, metric: str) -> str:
    return f"{source}::{metric}"


def evaluate_escalations(
    results: List[MetricResult],
    state_path: str,
    threshold: int = 3,
) -> List[EscalationAlert]:
    """Update escalation state and return alerts for metrics exceeding *threshold* consecutive unhealthy runs."""
    state = _load_state(state_path)
    alerts: List[EscalationAlert] = []

    for result in results:
        k = _key(result.source, result.metric.name)
        entry = state.get(k, EscalationState(source=result.source, metric=result.metric.name))

        if result.status != MetricStatus.OK:
            entry.consecutive_unhealthy += 1
            entry.last_status = result.status
            if entry.consecutive_unhealthy >= threshold:
                alerts.append(EscalationAlert(
                    source=result.source,
                    metric=result.metric.name,
                    consecutive_count=entry.consecutive_unhealthy,
                    status=result.status,
                ))
        else:
            entry.consecutive_unhealthy = 0
            entry.last_status = MetricStatus.OK

        state[k] = entry

    _save_state(state_path, state)
    return alerts


def format_escalation_report(alerts: List[EscalationAlert]) -> str:
    if not alerts:
        return "No escalation alerts."
    return "\n".join(str(a) for a in alerts)
