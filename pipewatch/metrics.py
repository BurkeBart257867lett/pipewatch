"""Metric collection and evaluation for pipeline health checks."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    name: str
    value: float
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: Optional[str] = None

    def __repr__(self) -> str:
        unit_str = f" {self.unit}" if self.unit else ""
        return f"Metric({self.source}/{self.name}={self.value}{unit_str})"


@dataclass
class MetricResult:
    metric: Metric
    status: MetricStatus
    message: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.status == MetricStatus.OK


def evaluate_metric(
    metric: Metric,
    warning_threshold: Optional[float] = None,
    critical_threshold: Optional[float] = None,
) -> MetricResult:
    """Evaluate a metric against optional warning and critical thresholds.

    Thresholds are treated as upper bounds (value >= threshold triggers alert).
    """
    if critical_threshold is not None and metric.value >= critical_threshold:
        return MetricResult(
            metric=metric,
            status=MetricStatus.CRITICAL,
            message=(
                f"{metric.name} is {metric.value} "
                f"(critical threshold: {critical_threshold})"
            ),
        )
    if warning_threshold is not None and metric.value >= warning_threshold:
        return MetricResult(
            metric=metric,
            status=MetricStatus.WARNING,
            message=(
                f"{metric.name} is {metric.value} "
                f"(warning threshold: {warning_threshold})"
            ),
        )
    return MetricResult(
        metric=metric,
        status=MetricStatus.OK,
        message=f"{metric.name} is {metric.value} — within acceptable range",
    )
