"""Tests for pipewatch.webhook."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.webhook import WebhookConfig, WebhookResult, _build_payload, send_webhook


def _make_metric(name="row_count", source="db", tags=None):
    return Metric(name=name, source=source, query="SELECT 1", tags=tags or [])


def _make_result(status=MetricStatus.WARNING, value=5.0, name="row_count", tags=None):
    m = _make_metric(name=name, tags=tags)
    return MetricResult(metric=m, status=status, value=value)


def _make_alert(status=MetricStatus.WARNING, value=5.0, name="row_count", tags=None):
    result = _make_result(status=status, value=value, name=name, tags=tags)
    return Alert(result=result, message=f"{name} is {status.value}")


def _default_config(url="http://example.com/hook"):
    return WebhookConfig(url=url)


# --- _build_payload ---

def test_build_payload_empty_alerts():
    payload = _build_payload([], _default_config())
    assert payload["count"] == 0
    assert payload["alerts"] == []


def test_build_payload_includes_metric_and_status():
    alert = _make_alert()
    payload = _build_payload([alert], _default_config())
    assert payload["count"] == 1
    entry = payload["alerts"][0]
    assert entry["metric"] == "row_count"
    assert entry["status"] == MetricStatus.WARNING.value


def test_build_payload_includes_source_by_default():
    alert = _make_alert()
    payload = _build_payload([alert], _default_config())
    assert "source" in payload["alerts"][0]


def test_build_payload_omits_source_when_disabled():
    cfg = WebhookConfig(url="http://x", include_source=False)
    alert = _make_alert()
    payload = _build_payload([alert], cfg)
    assert "source" not in payload["alerts"][0]


def test_build_payload_includes_tags_when_present():
    alert = _make_alert(tags=["env:prod"])
    payload = _build_payload([alert], _default_config())
    assert payload["alerts"][0]["tags"] == ["env:prod"]


def test_build_payload_omits_tags_when_disabled():
    cfg = WebhookConfig(url="http://x", include_tags=False)
    alert = _make_alert(tags=["env:prod"])
    payload = _build_payload([alert], cfg)
    assert "tags" not in payload["alerts"][0]


# --- send_webhook ---

def test_send_webhook_returns_success_on_empty_alerts():
    result = send_webhook([], _default_config())
    assert result.success is True
    assert result.status_code == 0


def test_send_webhook_success():
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_webhook([_make_alert()], _default_config())

    assert result.success is True
    assert result.status_code == 200


def test_send_webhook_http_error():
    import urllib.error
    err = urllib.error.HTTPError(url="http://x", code=500, msg="Server Error", hdrs=None, fp=None)  # type: ignore
    with patch("urllib.request.urlopen", side_effect=err):
        result = send_webhook([_make_alert()], _default_config())

    assert result.success is False
    assert result.status_code == 500


def test_send_webhook_connection_error():
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        result = send_webhook([_make_alert()], _default_config())

    assert result.success is False
    assert "connection refused" in result.error


def test_webhook_result_str_success():
    r = WebhookResult(url="http://x", success=True, status_code=200)
    assert "200" in str(r)


def test_webhook_result_str_failure():
    r = WebhookResult(url="http://x", success=False, error="timeout")
    assert "timeout" in str(r)
