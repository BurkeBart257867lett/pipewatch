"""Tests for pipewatch.routing."""
import pytest

from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
from pipewatch.routing import (
    RouteRule,
    format_routing_report,
    route_alerts,
)


def _make_alert(
    source: str = "src",
    metric: str = "m",
    status: MetricStatus = MetricStatus.WARNING,
    tags: list | None = None,
) -> Alert:
    return Alert(source=source, metric=metric, status=status, value=1.0, tags=tags or [])


# --- RouteRule.matches ---

def test_rule_matches_any_when_all_empty():
    rule = RouteRule(channel="c")
    assert rule.matches(_make_alert())


def test_rule_matches_by_source():
    rule = RouteRule(channel="c", sources=["db"])
    assert rule.matches(_make_alert(source="db"))
    assert not rule.matches(_make_alert(source="api"))


def test_rule_matches_by_status():
    rule = RouteRule(channel="c", statuses=["critical"])
    assert rule.matches(_make_alert(status=MetricStatus.CRITICAL))
    assert not rule.matches(_make_alert(status=MetricStatus.WARNING))


def test_rule_matches_by_tags():
    rule = RouteRule(channel="c", tags=["pii"])
    assert rule.matches(_make_alert(tags=["pii", "prod"]))
    assert not rule.matches(_make_alert(tags=["prod"]))


def test_rule_to_dict_roundtrip():
    rule = RouteRule(channel="ops", sources=["db"], statuses=["critical"], tags=["pii"])
    restored = RouteRule.from_dict(rule.to_dict())
    assert restored.channel == rule.channel
    assert restored.sources == rule.sources
    assert restored.statuses == rule.statuses
    assert restored.tags == rule.tags


# --- route_alerts ---

def test_route_to_default_when_no_rules():
    alerts = [_make_alert()]
    routed = route_alerts(alerts, rules=[], default_channel="fallback")
    assert "fallback" in routed
    assert len(routed["fallback"]) == 1


def test_route_first_matching_rule_wins():
    r1 = RouteRule(channel="ops", sources=["db"])
    r2 = RouteRule(channel="dev", sources=["db"])
    alerts = [_make_alert(source="db")]
    routed = route_alerts(alerts, rules=[r1, r2])
    assert "ops" in routed
    assert "dev" not in routed


def test_route_splits_to_multiple_channels():
    r_db = RouteRule(channel="ops", sources=["db"])
    r_api = RouteRule(channel="dev", sources=["api"])
    alerts = [_make_alert(source="db"), _make_alert(source="api")]
    routed = route_alerts(alerts, rules=[r_db, r_api])
    assert len(routed["ops"]) == 1
    assert len(routed["dev"]) == 1


def test_route_empty_alerts_returns_empty():
    routed = route_alerts([], rules=[], default_channel="default")
    assert routed == {}


# --- format_routing_report ---

def test_format_report_no_alerts():
    report = format_routing_report({})
    assert "No alerts" in report


def test_format_report_shows_channel_and_count():
    alert = _make_alert(source="db", metric="row_count")
    routed = {"ops": [alert]}
    report = format_routing_report(routed)
    assert "[ops]" in report
    assert "1 alert" in report
