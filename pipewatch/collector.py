"""Collector that gathers metrics from configured sources."""

import logging
from typing import List

from pipewatch.config import PipewatchConfig, SourceConfig
from pipewatch.metrics import Metric, MetricResult, evaluate_metric

logger = logging.getLogger(__name__)


def _collect_from_source(source: SourceConfig) -> List[Metric]:
    """Simulate metric collection from a source.

    In a real implementation this would query the source's API or database.
    Returns a list of Metric objects for the source.
    """
    # Placeholder: real adapters would be selected based on source.type
    logger.debug("Collecting metrics from source '%s' (type=%s)", source.name, source.type)
    return [
        Metric(name="row_count", value=0.0, source=source.name, unit="rows"),
        Metric(name="latency_seconds", value=0.0, source=source.name, unit="s"),
    ]


def collect_all(config: PipewatchConfig) -> List[MetricResult]:
    """Collect and evaluate metrics for every source defined in config."""
    results: List[MetricResult] = []

    for source in config.sources:
        try:
            metrics = _collect_from_source(source)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to collect from source '%s': %s", source.name, exc)
            continue

        for metric in metrics:
            thresholds = (source.thresholds or {}).get(metric.name, {})
            result = evaluate_metric(
                metric,
                warning_threshold=thresholds.get("warning"),
                critical_threshold=thresholds.get("critical"),
            )
            logger.debug("[%s] %s", result.status.value.upper(), result.message)
            results.append(result)

    return results
