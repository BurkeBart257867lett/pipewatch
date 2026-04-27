# Runbook CLI Integration

The `runbook` subcommand lets you attach remediation URLs to specific
`source/metric` pairs so that on-call engineers can quickly find guidance
when an alert fires.

## Registering the subcommand

```python
# pipewatch/cli.py  (excerpt)
from pipewatch.cli_runbook import add_runbook_subcommand

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipewatch")
    sub = parser.add_subparsers(dest="command", required=True)
    # ... existing subcommands ...
    add_runbook_subcommand(sub)
    return parser
```

## Usage

### Add a runbook link

```bash
pipewatch runbook add db row_count https://wiki.example.com/db-rows --note "Check ETL job"
# Runbook registered: [db/row_count] -> https://wiki.example.com/db-rows
```

### Show runbook for a specific metric

```bash
pipewatch runbook show db row_count
# [db/row_count] https://wiki.example.com/db-rows
#   note: Check ETL job
```

### List all registered runbooks

```bash
pipewatch runbook list
# [db/row_count] https://wiki.example.com/db-rows
#   note: Check ETL job
# [api/latency] https://wiki.example.com/api-latency
```

### Remove a runbook

```bash
pipewatch runbook remove db row_count
# Runbook removed: [db/row_count]
```

## Storage

Runbooks are persisted in `runbooks.json` (configurable via
`--runbook-file`).  Each entry is a JSON object with `source`, `metric`,
`url`, and optional `note` fields.  Adding an entry for an existing
`source/metric` pair replaces the previous record.

## Programmatic API

```python
from pathlib import Path
from pipewatch.runbook import add_runbook, lookup_runbook, RunbookEntry

path = Path("runbooks.json")
add_runbook(path, RunbookEntry(source="db", metric="row_count",
                               url="https://wiki/db", note="ETL"))
entry = lookup_runbook(path, "db", "row_count")
if entry:
    print(entry.url)
```
