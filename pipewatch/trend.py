"""Trend analysis: compare recent metric results against historical averages."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from pipewatch.metrics import MetricResult
from pipewatch.history import load_history


@dataclass
class TrendSummary:
    source: str
    metric_name: str
    current_value: float
    average_value: float
    delta_pct: float  # positive = above average
    window: int

    def __str__(self) -> str:
        direction = "above" if self.delta_pct >= 0 else "below"
        return (
            f"[{self.source}/{self.metric_name}] current={self.current_value:.3f} "
            f"avg={self.average_value:.3f} ({abs(self.delta_pct):.1f}% {direction} "
            f"{self.window}-run average)"
        )


def compute_trends(
    results: List[MetricResult],
    history_path: str,
    window: int = 10,
) -> List[TrendSummary]:
    """Return trend summaries for each result that has enough history."""
    entries = load_history(history_path)
    summaries: List[TrendSummary] = []

    for result in results:
        historical_values: List[float] = []
        for entry in entries:
            for hr in entry.results:
                if hr.source == result.source and hr.metric.name == result.metric.name:
                    if hr.value is not None:
                        historical_values.append(hr.value)

        recent = historical_values[-window:] if len(historical_values) >= window else historical_values
        if not recent or result.value is None:
            continue

        avg = sum(recent) / len(recent)
        if avg == 0:
            delta_pct = 0.0
        else:
            delta_pct = ((result.value - avg) / avg) * 100

        summaries.append(
            TrendSummary(
                source=result.source,
                metric_name=result.metric.name,
                current_value=result.value,
                average_value=avg,
                delta_pct=delta_pct,
                window=len(recent),
            )
        )

    return summaries


def format_trend_report(summaries: List[TrendSummary]) -> str:
    if not summaries:
        return "No trend data available."
    lines = ["Trend Report:"] + [f"  {s}" for s in summaries]
    return "\n".join(lines)
