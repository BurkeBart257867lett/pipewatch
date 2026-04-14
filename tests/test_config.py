"""Tests for pipewatch configuration loader."""

import os
import textwrap

import pytest

from pipewatch.config import SourceConfig, PipewatchConfig, load_config


@pytest.fixture
def config_file(tmp_path):
    """Factory fixture that writes a YAML config and returns its path."""
    def _write(content: str) -> str:
        p = tmp_path / "config.yaml"
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


def test_load_valid_config(config_file):
    path = config_file("""
        check_interval_seconds: 30
        log_level: DEBUG
        sources:
          - name: prod_postgres
            type: postgres
            connection:
              host: localhost
              port: 5432
              dbname: analytics
            alert_thresholds:
              row_count_min: 1000
    """)
    cfg = load_config(path)
    assert isinstance(cfg, PipewatchConfig)
    assert cfg.check_interval_seconds == 30
    assert cfg.log_level == "DEBUG"
    assert len(cfg.sources) == 1
    src = cfg.sources[0]
    assert isinstance(src, SourceConfig)
    assert src.name == "prod_postgres"
    assert src.type == "postgres"
    assert src.connection["port"] == 5432
    assert src.alert_thresholds["row_count_min"] == 1000


def test_defaults_when_fields_omitted(config_file):
    path = config_file("""
        sources:
          - name: simple_source
            type: csv
    """)
    cfg = load_config(path)
    assert cfg.check_interval_seconds == 60
    assert cfg.log_level == "INFO"
    assert cfg.sources[0].connection == {}
    assert cfg.sources[0].alert_thresholds == {}


def test_empty_config_file(config_file):
    path = config_file("")
    cfg = load_config(path)
    assert cfg.sources == []


def test_missing_config_file():
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config("/nonexistent/path/config.yaml")


def test_source_missing_name(config_file):
    path = config_file("""
        sources:
          - type: postgres
    """)
    with pytest.raises(ValueError, match="'name'"):
        load_config(path)


def test_source_missing_type(config_file):
    path = config_file("""
        sources:
          - name: broken_source
    """)
    with pytest.raises(ValueError, match="'type'"):
        load_config(path)
