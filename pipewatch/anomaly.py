"""Simple anomaly detection using z-score over historical metric values."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import statistics

from pipewatch.metrics import MetricResult
from pipewatch.history import HistoryEntry


@dataclass
class AnomalyAlert:
    source: str
    metric_name: str
    current_value: float
    mean: float
    stddev: float
    z_score: float
    threshold: float

    def __str__(self) -> str:
        return (
            f"[ANOMALY] {self.source}/{self.metric_name}: "
            f"value={self.current_value:.4g}, z={self.z_score:.2f} "
            f"(mean={self.mean:.4g}, stddev={self.stddev:.4g})"
        )


def _extract_values(entries: List[HistoryEntry], source: str, metric_name: str) -> List[float]:
    values: List[float] = []
    for entry in entries:
        for result in entry.results:
            if result.source == source and result.metric.name == metric_name:
                values.append(result.value)
    return values


def detect_anomalies(
    current_results: List[MetricResult],
    history: List[HistoryEntry],
    z_threshold: float = 2.5,
    min_history: int = 5,
) -> List[AnomalyAlert]:
    alerts: List[AnomalyAlert] = []
    for result in current_results:
        values = _extract_values(history, result.source, result.metric.name)
        if len(values) < min_history:
            continue
        mean = statistics.mean(values)
        stddev = statistics.pstdev(values)
        if stddev == 0:
            continue
        z = (result.value - mean) / stddev
        if abs(z) >= z_threshold:
            alerts.append(AnomalyAlert(
                source=result.source,
                metric_name=result.metric.name,
                current_value=result.value,
                mean=mean,
                stddev=stddev,
                z_score=z,
                threshold=z_threshold,
            ))
    return alerts


def format_anomaly_report(alerts: List[AnomalyAlert]) -> str:
    if not alerts:
        return "No anomalies detected."
    lines = [f"Anomalies detected ({len(alerts)}):"] + [f"  {a}" for a in alerts]
    return "\n".join(lines)
