# Silence Sub-command Integration

The `silence` sub-command lets operators suppress alerts for specific
`source/metric` pairs during planned maintenance windows.

## Registering with the main CLI

In `pipewatch/cli.py`, import and register the sub-command:

```python
from pipewatch.cli_silencer import add_silence_subcommand

def build_parser():
    parser = ArgumentParser(prog="pipewatch", ...)
    sub = parser.add_subparsers(dest="cmd", required=True)
    # ... existing sub-commands ...
    add_silence_subcommand(sub)
    return parser
```

## Usage examples

```bash
# Silence indefinitely
pipewatch silence add my_db row_count "scheduled migration"

# Silence until a specific time (UTC ISO-8601)
pipewatch silence add my_db row_count "deploy window" \
    --expires-at 2025-06-01T06:00:00+00:00

# List all currently active silences
pipewatch silence list

# Remove a silence rule
pipewatch silence remove my_db row_count
```

## Filtering alerts with silences

In `pipewatch/alerts.py` (or `reporter.py`) call `is_silenced` before
emitting an alert:

```python
from pipewatch.silencer import is_silenced

filtered = [
    a for a in alerts
    if not is_silenced(a.source, a.metric_name)
]
```

## Storage

Rules are persisted in `.pipewatch_silences.json` (configurable via
`--silence-file`).  Expired rules remain on disk but are ignored by
`is_silenced` and `list_active_silences`; a future `prune` command can
clean them up.
