"""Alert evaluation and formatting for pipewatch."""

from dataclasses import dataclass
from typing import List

from pipewatch.metrics import MetricResult, MetricStatus


@dataclass
class Alert:
    """Represents a triggered alert for a metric result."""

    source: str
    metric_name: str
    status: MetricStatus
    value: float
    message: str

    def __str__(self) -> str:
        icon = "\u26a0\ufe0f" if self.status == MetricStatus.WARNING else "\U0001f6a8"
        return (
            f"{icon} [{self.status.value.upper()}] {self.source}/{self.metric_name} "
            f"= {self.value} — {self.message}"
        )


def evaluate_alerts(results: List[MetricResult]) -> List[Alert]:
    """Return alerts for any metric results that are not healthy."""
    alerts: List[Alert] = []
    for result in results:
        if result.status == MetricStatus.OK:
            continue

        metric = result.metric
        if result.status == MetricStatus.WARNING:
            threshold = metric.warning_threshold
            message = (
                f"Value exceeds warning threshold of {threshold}"
                if threshold is not None
                else "Warning condition met"
            )
        else:
            threshold = metric.critical_threshold
            message = (
                f"Value exceeds critical threshold of {threshold}"
                if threshold is not None
                else "Critical condition met"
            )

        alerts.append(
            Alert(
                source=result.source,
                metric_name=metric.name,
                status=result.status,
                value=result.value,
                message=message,
            )
        )
    return alerts


def format_alert_summary(alerts: List[Alert]) -> str:
    """Format a human-readable summary of all alerts."""
    if not alerts:
        return "\u2705 All metrics healthy."
    lines = [f"Found {len(alerts)} alert(s):"] + [str(a) for a in alerts]
    return "\n".join(lines)
