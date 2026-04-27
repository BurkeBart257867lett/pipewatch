"""Tests for pipewatch.runbook."""
import json
import pytest
from pathlib import Path

from pipewatch.runbook import (
    RunbookEntry,
    add_runbook,
    remove_runbook,
    lookup_runbook,
    load_runbooks,
    format_runbook_list,
)


@pytest.fixture
def rfile(tmp_path: Path) -> Path:
    return tmp_path / "runbooks.json"


def test_load_empty_when_missing(rfile):
    assert load_runbooks(rfile) == []


def test_add_and_load(rfile):
    entry = RunbookEntry(source="db", metric="row_count", url="https://wiki/db-rows")
    add_runbook(rfile, entry)
    entries = load_runbooks(rfile)
    assert len(entries) == 1
    assert entries[0].source == "db"
    assert entries[0].metric == "row_count"
    assert entries[0].url == "https://wiki/db-rows"


def test_add_overwrites_existing(rfile):
    e1 = RunbookEntry(source="db", metric="row_count", url="https://old")
    e2 = RunbookEntry(source="db", metric="row_count", url="https://new", note="updated")
    add_runbook(rfile, e1)
    add_runbook(rfile, e2)
    entries = load_runbooks(rfile)
    assert len(entries) == 1
    assert entries[0].url == "https://new"
    assert entries[0].note == "updated"


def test_remove_existing(rfile):
    entry = RunbookEntry(source="api", metric="latency", url="https://wiki/latency")
    add_runbook(rfile, entry)
    removed = remove_runbook(rfile, "api", "latency")
    assert removed is True
    assert load_runbooks(rfile) == []


def test_remove_missing_returns_false(rfile):
    removed = remove_runbook(rfile, "api", "latency")
    assert removed is False


def test_lookup_found(rfile):
    entry = RunbookEntry(source="s3", metric="file_age", url="https://wiki/s3")
    add_runbook(rfile, entry)
    result = lookup_runbook(rfile, "s3", "file_age")
    assert result is not None
    assert result.url == "https://wiki/s3"


def test_lookup_not_found(rfile):
    assert lookup_runbook(rfile, "x", "y") is None


def test_format_runbook_list_empty():
    assert format_runbook_list([]) == "No runbooks registered."


def test_format_runbook_list_with_entries():
    entries = [
        RunbookEntry(source="db", metric="rows", url="https://a"),
        RunbookEntry(source="api", metric="latency", url="https://b", note="check SLA"),
    ]
    out = format_runbook_list(entries)
    assert "[db/rows]" in out
    assert "https://a" in out
    assert "check SLA" in out


def test_entry_str_no_note():
    e = RunbookEntry(source="db", metric="rows", url="https://wiki")
    assert str(e) == "[db/rows] https://wiki"


def test_entry_str_with_note():
    e = RunbookEntry(source="db", metric="rows", url="https://wiki", note="see oncall")
    assert "note: see oncall" in str(e)


def test_roundtrip_serialisation(rfile):
    entry = RunbookEntry(source="kafka", metric="lag", url="https://wiki/lag", note="critical")
    add_runbook(rfile, entry)
    raw = json.loads(rfile.read_text())
    assert raw[0]["source"] == "kafka"
    assert raw[0]["note"] == "critical"
