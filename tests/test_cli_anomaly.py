"""Tests for pipewatch.cli_anomaly."""
from __future__ import annotations
import argparse
from unittest.mock import patch, MagicMock
from pipewatch.cli_anomaly import cmd_anomaly, add_anomaly_subcommand
from pipewatch.anomaly import AnomalyAlert


def _make_args(**kwargs):
    defaults = dict(config="pipewatch.yaml", history_file="pipewatch_history.json",
                    z_threshold=2.5, min_history=5, exit_code=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_anomaly_subcommand_registers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_anomaly_subcommand(sub)
    args = parser.parse_args(["anomaly"])
    assert hasattr(args, "func")


def test_cmd_anomaly_no_alerts(capsys):
    with patch("pipewatch.cli_anomaly.load_config") as lc, \
         patch("pipewatch.cli_anomaly.collect_all", return_value=[]) as ca, \
         patch("pipewatch.cli_anomaly.load_history", return_value=[]) as lh, \
         patch("pipewatch.cli_anomaly.detect_anomalies", return_value=[]) as da:
        cmd_anomaly(_make_args())
        out = capsys.readouterr().out
        assert "No anomalies" in out


def test_cmd_anomaly_with_alerts(capsys):
    alert = AnomalyAlert(source="db", metric_name="lag", current_value=99,
                         mean=10, stddev=2, z_score=44.5, threshold=2.5)
    with patch("pipewatch.cli_anomaly.load_config"), \
         patch("pipewatch.cli_anomaly.collect_all", return_value=[]), \
         patch("pipewatch.cli_anomaly.load_history", return_value=[]), \
         patch("pipewatch.cli_anomaly.detect_anomalies", return_value=[alert]):
        cmd_anomaly(_make_args())
        out = capsys.readouterr().out
        assert "ANOMALY" in out


def test_cmd_anomaly_exit_code_on_alerts():
    alert = AnomalyAlert(source="db", metric_name="lag", current_value=99,
                         mean=10, stddev=2, z_score=44.5, threshold=2.5)
    with patch("pipewatch.cli_anomaly.load_config"), \
         patch("pipewatch.cli_anomaly.collect_all", return_value=[]), \
         patch("pipewatch.cli_anomaly.load_history", return_value=[]), \
         patch("pipewatch.cli_anomaly.detect_anomalies", return_value=[alert]):
        try:
            cmd_anomaly(_make_args(exit_code=True))
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2


def test_cmd_anomaly_no_exit_when_no_alerts():
    with patch("pipewatch.cli_anomaly.load_config"), \
         patch("pipewatch.cli_anomaly.collect_all", return_value=[]), \
         patch("pipewatch.cli_anomaly.load_history", return_value=[]), \
         patch("pipewatch.cli_anomaly.detect_anomalies", return_value=[]):
        cmd_anomaly(_make_args(exit_code=True))  # should not raise
