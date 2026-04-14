"""Configuration loader for pipewatch.

Loads and validates pipeline source configurations from a YAML file.
"""

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.pipewatch/config.yaml")


@dataclass
class SourceConfig:
    name: str
    type: str
    connection: dict[str, Any] = field(default_factory=dict)
    alert_thresholds: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipewatchConfig:
    sources: list[SourceConfig] = field(default_factory=list)
    check_interval_seconds: int = 60
    log_level: str = "INFO"


def load_config(path: str = DEFAULT_CONFIG_PATH) -> PipewatchConfig:
    """Load and parse the pipewatch configuration file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A PipewatchConfig instance populated from the file.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If required fields are missing or invalid.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Run `pipewatch init` to create a default configuration."
        )

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    sources = []
    for entry in raw.get("sources", []):
        if "name" not in entry:
            raise ValueError("Each source must have a 'name' field.")
        if "type" not in entry:
            raise ValueError(f"Source '{entry['name']}' is missing the 'type' field.")
        sources.append(
            SourceConfig(
                name=entry["name"],
                type=entry["type"],
                connection=entry.get("connection", {}),
                alert_thresholds=entry.get("alert_thresholds", {}),
            )
        )

    return PipewatchConfig(
        sources=sources,
        check_interval_seconds=raw.get("check_interval_seconds", 60),
        log_level=raw.get("log_level", "INFO"),
    )
