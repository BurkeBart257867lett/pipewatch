# Anomaly Detection Integration

The `anomaly` subcommand detects statistical anomalies in current pipeline metrics
by comparing them against historical values using a **z-score** approach.

## Usage

```bash
pipewatch anomaly [--config CONFIG] [--history-file FILE] \
                  [--z-threshold FLOAT] [--min-history INT] [--exit-code]
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | `pipewatch.yaml` | Path to config file |
| `--history-file` | `pipewatch_history.json` | History file to read |
| `--z-threshold` | `2.5` | Z-score cutoff for anomaly |
| `--min-history` | `5` | Minimum data points required |
| `--exit-code` | off | Exit with code `2` if anomalies found |

## How It Works

1. Current metrics are collected via `collect_all`.
2. Historical values for each `(source, metric)` pair are extracted from the history file.
3. If at least `--min-history` points exist and stddev > 0, a z-score is computed.
4. Any result with `|z| >= z_threshold` is reported as an anomaly.

## Output

Each detected anomaly is printed to stdout in the following format:

```
ANOMALY  <source>.<metric>  current=<value>  z=<score>  (mean=<mean>, stddev=<stddev>)
```

If no anomalies are detected, the command exits silently with code `0`.
If `--exit-code` is set and anomalies are found, the exit code is `2`.

## Registering the Subcommand

In `pipewatch/cli.py`, add:

```python
from pipewatch.cli_anomaly import add_anomaly_subcommand
# inside build_parser:
add_anomaly_subcommand(subparsers)
```
