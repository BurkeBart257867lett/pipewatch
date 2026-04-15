"""CLI-facing reporter that ties together collection, evaluation, and alerting."""

from typing import List, Tuple

from pipewatch.collector import collect_all
from pipewatch.config import PipewatchConfig
from pipewatch.metrics import MetricResult
from pipewatch.alerts import Alert, evaluate_alerts, format_alert_summary


def run_report(config: PipewatchConfig) -> Tuple[List[MetricResult], List[Alert]]:
    """Collect all metrics, evaluate alerts, and return results and alerts."""
    results = collect_all(config)
    alerts = evaluate_alerts(results)
    return results, alerts


def print_report(config: PipewatchConfig, verbose: bool = False) -> int:
    """Run the full pipeline report and print output to stdout.

    Returns exit code: 0 if all healthy, 1 if warnings present, 2 if critical.
    """
    results, alerts = run_report(config)

    if verbose:
        print("Metric Results:")
        for r in results:
            icon = "\u2705" if r.is_healthy() else "\u274c"
            print(f"  {icon} {r.source}/{r.metric.name} = {r.value} [{r.status.value}]")
        print()

    print(format_alert_summary(alerts))

    if any(a.status.value == "critical" for a in alerts):
        return 2
    if alerts:
        return 1
    return 0
