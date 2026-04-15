"""Tests for pipewatch.cli module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from pipewatch.cli import build_parser, cmd_run, cmd_history
from pipewatch.metrics import MetricStatus


@pytest.fixture
def parser():
    return build_parser()


def _mock_result(status=MetricStatus.OK, source="src", name="lag", value=0.0):
    metric = MagicMock()
    metric.source = source
    metric.name = name
    r = MagicMock()
    r.metric = metric
    r.value = value
    r.status = status
    return r


def test_parser_run_defaults(parser):
    args = parser.parse_args(["run"])
    assert args.command == "run"
    assert args.save_history is False
    assert args.history_path is None


def test_parser_history_defaults(parser):
    args = parser.parse_args(["history"])
    assert args.command == "history"
    assert args.limit == 50
    assert args.source is None


def test_parser_history_with_filters(parser):
    args = parser.parse_args(["history", "--source", "kafka", "--metric", "lag", "--limit", "10"])
    assert args.source == "kafka"
    assert args.metric == "lag"
    assert args.limit == 10


def test_cmd_run_returns_0_when_no_alerts(tmp_path):
    args = MagicMock()
    args.config = str(tmp_path / "pipewatch.yaml")
    args.save_history = False
    results = [_mock_result(status=MetricStatus.OK)]
    with patch("pipewatch.cli.load_config"), \
         patch("pipewatch.cli.collect_all", return_value=results), \
         patch("pipewatch.cli.run_report"), \
         patch("pipewatch.cli.print_report"), \
         patch("pipewatch.cli.evaluate_alerts", return_value=[]):
        code = cmd_run(args)
    assert code == 0


def test_cmd_run_returns_1_when_alerts(tmp_path):
    args = MagicMock()
    args.config = str(tmp_path / "pipewatch.yaml")
    args.save_history = False
    results = [_mock_result(status=MetricStatus.CRITICAL)]
    alert = MagicMock()
    with patch("pipewatch.cli.load_config"), \
         patch("pipewatch.cli.collect_all", return_value=results), \
         patch("pipewatch.cli.run_report"), \
         patch("pipewatch.cli.print_report"), \
         patch("pipewatch.cli.evaluate_alerts", return_value=[alert]), \
         patch("pipewatch.cli.format_alert_summary", return_value="ALERT"):
        code = cmd_run(args)
    assert code == 1


def test_cmd_run_saves_history(tmp_path):
    args = MagicMock()
    args.config = str(tmp_path / "pipewatch.yaml")
    args.save_history = True
    args.history_path = str(tmp_path / "hist.json")
    results = [_mock_result()]
    with patch("pipewatch.cli.load_config"), \
         patch("pipewatch.cli.collect_all", return_value=results), \
         patch("pipewatch.cli.run_report"), \
         patch("pipewatch.cli.print_report"), \
         patch("pipewatch.cli.evaluate_alerts", return_value=[]) as _, \
         patch("pipewatch.cli.append_results") as mock_append:
        cmd_run(args)
    mock_append.assert_called_once()


def test_cmd_history_no_entries(tmp_path, capsys):
    args = MagicMock()
    args.history_path = str(tmp_path / "empty.json")
    args.source = None
    args.metric = None
    args.limit = 50
    with patch("pipewatch.cli.load_history", return_value=[]):
        code = cmd_history(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "No history found" in captured.out
