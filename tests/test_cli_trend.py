"""Tests for pipewatch.cli_trend."""
import argparse
import pytest
from unittest.mock import patch, MagicMock
from pipewatch.cli_trend import cmd_trend, add_trend_subcommand
from pipewatch.trend import TrendSummary


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_trend_subcommand(sub)
    return p


def _make_summary(source="db", name="rows", delta=5.0):
    return TrendSummary(
        source=source, metric_name=name,
        current_value=105.0, average_value=100.0,
        delta_pct=delta, window=5,
    )


def test_add_trend_subcommand_registers(parser):
    args = parser.parse_args(["trend"])
    assert hasattr(args, "func")


def test_trend_defaults(parser):
    args = parser.parse_args(["trend"])
    assert args.window == 10
    assert args.source is None
    assert args.threshold is None


def test_cmd_trend_prints_report(capsys):
    args = argparse.Namespace(
        config="pipewatch.yaml", history="h.json",
        window=5, source=None, threshold=None,
    )
    summaries = [_make_summary()]
    with patch("pipewatch.cli_trend.load_config"), \
         patch("pipewatch.cli_trend.collect_all", return_value=[]), \
         patch("pipewatch.cli_trend.compute_trends", return_value=summaries):
        cmd_trend(args)
    out = capsys.readouterr().out
    assert "Trend Report" in out


def test_cmd_trend_filters_by_source(capsys):
    args = argparse.Namespace(
        config="pipewatch.yaml", history="h.json",
        window=5, source="other", threshold=None,
    )
    summaries = [_make_summary(source="db")]
    with patch("pipewatch.cli_trend.load_config"), \
         patch("pipewatch.cli_trend.collect_all", return_value=[]), \
         patch("pipewatch.cli_trend.compute_trends", return_value=summaries):
        cmd_trend(args)
    out = capsys.readouterr().out
    assert "No trend data" in out


def test_cmd_trend_filters_by_threshold(capsys):
    args = argparse.Namespace(
        config="pipewatch.yaml", history="h.json",
        window=5, source=None, threshold=50.0,
    )
    summaries = [_make_summary(delta=5.0)]
    with patch("pipewatch.cli_trend.load_config"), \
         patch("pipewatch.cli_trend.collect_all", return_value=[]), \
         patch("pipewatch.cli_trend.compute_trends", return_value=summaries):
        cmd_trend(args)
    out = capsys.readouterr().out
    assert "No trend data" in out
