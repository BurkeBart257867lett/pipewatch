"""Export pipeline metric results to various output formats."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.metrics import MetricResult


SUPPORTED_FORMATS = ("json", "csv", "text")


def _result_to_dict(result: MetricResult) -> dict:
    return {
        "source": result.metric.source,
        "name": result.metric.name,
        "value": result.value,
        "status": result.status.value,
        "warning_threshold": result.metric.warning_threshold,
        "critical_threshold": result.metric.critical_threshold,
    }


def export_json(results: List[MetricResult], indent: int = 2) -> str:
    """Serialize results to a JSON string."""
    return json.dumps([_result_to_dict(r) for r in results], indent=indent)


def export_csv(results: List[MetricResult]) -> str:
    """Serialize results to a CSV string."""
    fieldnames = ["source", "name", "value", "status", "warning_threshold", "critical_threshold"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(_result_to_dict(result))
    return buf.getvalue()


def export_text(results: List[MetricResult]) -> str:
    """Serialize results to a human-readable text table."""
    if not results:
        return "No results to display.\n"
    lines = [f"{'SOURCE':<20} {'METRIC':<25} {'VALUE':>10} {'STATUS':<10}"]
    lines.append("-" * 68)
    for r in results:
        lines.append(
            f"{r.metric.source:<20} {r.metric.name:<25} {r.value:>10.4g} {r.status.value:<10}"
        )
    return "\n".join(lines) + "\n"


def export_results(results: List[MetricResult], fmt: str) -> str:
    """Dispatch to the appropriate exporter based on *fmt*."""
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported export format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")
    if fmt == "json":
        return export_json(results)
    if fmt == "csv":
        return export_csv(results)
    return export_text(results)
