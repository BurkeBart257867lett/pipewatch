"""Tests for pipewatch.cli_routing."""
import json
from argparse import ArgumentParser
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.cli_routing import add_routing_subcommand, cmd_route
from pipewatch.metrics import MetricStatus


@pytest.fixture()
def parser():
    p = ArgumentParser()
    sub = p.add_subparsers(dest="subcommand")
    add_routing_subcommand(sub)
    return p


def _make_args(rules="routing_rules.json", default_channel="default", config="pw.yml"):
    args = MagicMock()
    args.rules = rules
    args.default_channel = default_channel
    args.config = config
    return args


def test_add_routing_subcommand_registers(parser):
    args = parser.parse_args(["route"])
    assert args.subcommand == "route"


def test_route_defaults(parser):
    args = parser.parse_args(["route"])
    assert args.rules == "routing_rules.json"
    assert args.default_channel == "default"


def test_cmd_route_no_alerts_returns_zero(tmp_path):
    args = _make_args(rules=str(tmp_path / "rules.json"))
    with (
        patch("pipewatch.cli_routing.load_config"),
        patch("pipewatch.cli_routing.collect_all", return_value=[]),
        patch("pipewatch.cli_routing.evaluate_alerts", return_value=[]),
        patch("builtins.print"),
    ):
        rc = cmd_route(args)
    assert rc == 0


def test_cmd_route_with_alerts_returns_one(tmp_path):
    from pipewatch.alerts import Alert

    alert = Alert(
        source="db", metric="lag", status=MetricStatus.CRITICAL, value=99.0, tags=[]
    )
    args = _make_args(rules=str(tmp_path / "rules.json"))
    with (
        patch("pipewatch.cli_routing.load_config"),
        patch("pipewatch.cli_routing.collect_all", return_value=[]),
        patch("pipewatch.cli_routing.evaluate_alerts", return_value=[alert]),
        patch("builtins.print"),
    ):
        rc = cmd_route(args)
    assert rc == 1


def test_cmd_route_loads_rules_from_file(tmp_path):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        json.dumps([{"channel": "ops", "sources": ["db"], "statuses": [], "tags": []}])
    )
    args = _make_args(rules=str(rules_file))
    with (
        patch("pipewatch.cli_routing.load_config"),
        patch("pipewatch.cli_routing.collect_all", return_value=[]),
        patch("pipewatch.cli_routing.evaluate_alerts", return_value=[]),
        patch("builtins.print"),
    ):
        rc = cmd_route(args)
    assert rc == 0
