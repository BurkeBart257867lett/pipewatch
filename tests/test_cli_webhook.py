"""Tests for pipewatch.cli_webhook."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.cli_webhook import add_webhook_subcommand, cmd_webhook
from pipewatch.webhook import WebhookResult
from pipewatch.metrics import MetricResult, MetricStatus, Metric
from pipewatch.alerts import Alert


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_webhook_subcommand(sub)
    return p


def _make_alert():
    m = Metric(name="lag", source="kafka", query="SELECT 1")
    r = MetricResult(metric=m, status=MetricStatus.CRITICAL, value=99.0)
    return Alert(result=r, message="lag is critical")


def test_add_webhook_subcommand_registers(parser):
    args = parser.parse_args(["webhook", "http://example.com/hook"])
    assert args.command == "webhook"
    assert args.url == "http://example.com/hook"


def test_webhook_defaults(parser):
    args = parser.parse_args(["webhook", "http://example.com"])
    assert args.method == "POST"
    assert args.timeout == 10
    assert args.no_source is False
    assert args.no_tags is False


def test_cmd_webhook_no_alerts_returns_zero(parser, capsys):
    args = parser.parse_args(["webhook", "http://example.com"])
    with patch("pipewatch.cli_webhook.load_config"), \
         patch("pipewatch.cli_webhook.collect_all", return_value=[]), \
         patch("pipewatch.cli_webhook.evaluate_alerts", return_value=[]):
        code = cmd_webhook(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "No alerts" in out


def test_cmd_webhook_success_returns_zero(parser, capsys):
    args = parser.parse_args(["webhook", "http://example.com"])
    alerts = [_make_alert()]
    ok_result = WebhookResult(url="http://example.com", success=True, status_code=200)
    with patch("pipewatch.cli_webhook.load_config"), \
         patch("pipewatch.cli_webhook.collect_all", return_value=[]), \
         patch("pipewatch.cli_webhook.evaluate_alerts", return_value=alerts), \
         patch("pipewatch.cli_webhook.send_webhook", return_value=ok_result):
        code = cmd_webhook(args)
    assert code == 0
    assert "1 alert" in capsys.readouterr().out


def test_cmd_webhook_failure_returns_one(parser, capsys):
    args = parser.parse_args(["webhook", "http://example.com"])
    alerts = [_make_alert()]
    fail_result = WebhookResult(url="http://example.com", success=False, error="refused")
    with patch("pipewatch.cli_webhook.load_config"), \
         patch("pipewatch.cli_webhook.collect_all", return_value=[]), \
         patch("pipewatch.cli_webhook.evaluate_alerts", return_value=alerts), \
         patch("pipewatch.cli_webhook.send_webhook", return_value=fail_result):
        code = cmd_webhook(args)
    assert code == 1
    assert "refused" in capsys.readouterr().err
