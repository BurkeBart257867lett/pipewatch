"""Check metric results against stored baselines and produce deviation alerts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.baseline import get_baseline, deviation_pct, DEFAULT_BASELINE_PATH
from pipewatch.metrics import MetricResult


@dataclass
class DeviationAlert:
    source: str
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_pct: float
    threshold_pct: float

    def __str__(self) -> str:
        sign = "+" if self.deviation_pct >= 0 else ""
        return (
            f"[BASELINE] {self.source}/{self.metric_name}: "
            f"{sign}{self.deviation_pct:.1f}% deviation "
            f"(current={self.current_value}, baseline={self.baseline_value})"
        )


def check_baselines(
    results: List[MetricResult],
    threshold_pct: float = 20.0,
    baseline_path: str = DEFAULT_BASELINE_PATH,
) -> List[DeviationAlert]:
    """Return DeviationAlerts for any result deviating beyond threshold_pct."""
    alerts: List[DeviationAlert] = []
    for result in results:
        entry = get_baseline(result.source, result.metric_name, baseline_path)
        if entry is None:
            continue
        pct = deviation_pct(result.value, entry.baseline_value)
        if pct is None:
            continue
        if abs(pct) >= threshold_pct:
            alerts.append(
                DeviationAlert(
                    source=result.source,
                    metric_name=result.metric_name,
                    current_value=result.value,
                    baseline_value=entry.baseline_value,
                    deviation_pct=round(pct, 4),
                    threshold_pct=threshold_pct,
                )
            )
    return alerts


def format_deviation_summary(alerts: List[DeviationAlert]) -> str:
    if not alerts:
        return "No baseline deviations detected."
    lines = [f"Baseline deviations ({len(alerts)} found):"] + [f"  {a}" for a in alerts]
    return "\n".join(lines)
