"""Metric correlation analysis across sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricResult


@dataclass
class CorrelationResult:
    source_a: str
    metric_a: str
    source_b: str
    metric_b: str
    coefficient: float  # Pearson r, range [-1, 1]
    sample_size: int

    def __str__(self) -> str:
        strength = _describe_strength(self.coefficient)
        return (
            f"{self.source_a}/{self.metric_a} <-> "
            f"{self.source_b}/{self.metric_b}: "
            f"r={self.coefficient:.3f} ({strength}, n={self.sample_size})"
        )


def _describe_strength(r: float) -> str:
    abs_r = abs(r)
    if abs_r >= 0.9:
        return "very strong"
    if abs_r >= 0.7:
        return "strong"
    if abs_r >= 0.4:
        return "moderate"
    if abs_r >= 0.2:
        return "weak"
    return "negligible"


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """Compute Pearson correlation coefficient for two equal-length lists."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _extract_series(
    entries: List[HistoryEntry],
) -> Dict[Tuple[str, str], List[float]]:
    """Return a dict mapping (source, metric_name) -> ordered list of values."""
    series: Dict[Tuple[str, str], List[float]] = {}
    for entry in sorted(entries, key=lambda e: e.timestamp):
        for result in entry.results:
            key = (result.metric.source, result.metric.name)
            series.setdefault(key, []).append(result.value)
    return series


def compute_correlations(
    entries: List[HistoryEntry],
    min_samples: int = 5,
    min_abs_r: float = 0.0,
) -> List[CorrelationResult]:
    """Compute pairwise Pearson correlations for all metric series in history."""
    series = _extract_series(entries)
    keys = list(series.keys())
    results: List[CorrelationResult] = []

    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ka, kb = keys[i], keys[j]
            xs, ys = series[ka], series[kb]
            n = min(len(xs), len(ys))
            if n < min_samples:
                continue
            r = _pearson(xs[:n], ys[:n])
            if r is None:
                continue
            if abs(r) < min_abs_r:
                continue
            results.append(
                CorrelationResult(
                    source_a=ka[0],
                    metric_a=ka[1],
                    source_b=kb[0],
                    metric_b=kb[1],
                    coefficient=round(r, 6),
                    sample_size=n,
                )
            )

    results.sort(key=lambda c: abs(c.coefficient), reverse=True)
    return results


def format_correlation_report(correlations: List[CorrelationResult]) -> str:
    if not correlations:
        return "No significant correlations found."
    lines = ["Metric Correlations:", "-" * 50]
    for c in correlations:
        lines.append(f"  {c}")
    return "\n".join(lines)
