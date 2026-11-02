"""Task 1 — domain models + deterministic NDJSON replay (FileConnector).

Covers the plan's test list for Task 1:
- read alert + archive events from the same file;
- select exactly the requested alert; missing/ambiguous -> typed errors;
- preserve _index/_id in raw_ref;
- filter by time window, host and query conditions;
- UTF-8 and escaped JSON strings;
- malformed NDJSON -> error with file name + line number, no partial results;
- repeated reads produce identical normalized records and order.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from soc_investigator.connectors.base import SiemConnector
from soc_investigator.connectors.file import FileConnector
from soc_investigator.errors import ConnectorError, ScenarioPackNotFound
from soc_investigator.models import Alert, Event, InvestigationReport

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = REPO_ROOT / "lab-data" / "sample-mini.ndjson"

ALERT_ID = "alert-phish-0001"
HOST = "WS-014"


def _write(tmp_path: Path, lines: list[str], name: str = "case.ndjson") -> Path:
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _hit(index: str, doc_id: str, source: dict) -> str:
    return json.dumps({"_index": index, "_id": doc_id, "_source": source}, ensure_ascii=False)


# ---------------------------------------------------------------- sample fixture


def test_sample_fixture_parses_as_ndjson() -> None:
    lines = [ln for ln in SAMPLE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 100
    for ln in lines:
        rec = json.loads(ln)
        assert {"_index", "_id", "_source"} <= set(rec)


def test_sample_fixture_has_exactly_one_alert() -> None:
    c = FileConnector(SAMPLE)
    alert = c.get_alert(ALERT_ID)
    assert isinstance(alert, Alert)
    assert alert.host == HOST


# ---------------------------------------------------------------- model contracts


def test_event_required_fields_and_optionals() -> None:
    ev = Event(
        document_id="d1",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        host=HOST,
        source="sysmon",
        raw_ref={"index": "i", "id": "d1"},
        raw={},
    )
    assert ev.command_line is None and ev.event_code is None


def test_report_roundtrip_is_stable() -> None:
    report = InvestigationReport.model_validate_json(
        (REPO_ROOT / "tests" / "fixtures" / "ndjson" / "report-minimal.json").read_text(
            encoding="utf-8"
        )
    )
    again = InvestigationReport.model_validate_json(report.model_dump_json())
    assert again == report
    assert again.schema_version == "0.2.6"


def test_report_rejects_missing_required_fields() -> None:
    bad = {"schema_version": "0.2.6"}
    with pytest.raises(Exception):
        InvestigationReport.model_validate(bad)


# ---------------------------------------------------------------- connector protocol


def test_fileconnector_implements_protocol() -> None:
    c: SiemConnector = FileConnector(SAMPLE)
    assert callable(c.get_alert) and callable(c.search_events) and callable(c.write_investigation)


# ---------------------------------------------------------------- get_alert


def test_get_alert_preserves_raw_ref() -> None:
    alert = FileConnector(SAMPLE).get_alert(ALERT_ID)
    assert alert.raw_ref.index == "wazuh-alerts-4.x-2026.10.31"
    assert alert.raw_ref.id == ALERT_ID
    assert alert.timestamp.tzinfo is not None


def test_get_alert_unknown_id_raises_typed_error() -> None:
    with pytest.raises(ScenarioPackNotFound):
        FileConnector(SAMPLE).get_alert("does-not-exist")


def test_get_alert_ambiguous_raises_connector_error(tmp_path: None) -> None:
    src = {"rule": {"id": "r1", "firedat": "2026-10-31T09:00:00Z"},
           "@timestamp": "2026-10-31T09:00:00Z",
           "agent": {"name": HOST}, "data": {}}
    dup = _hit("wazuh-alerts-x", "dup-1", src)
    p = _write(tmp_path, [dup, dup])
    with pytest.raises(ConnectorError, match="duplicate"):
        FileConnector(p).get_alert("dup-1")


def test_get_alert_from_same_file_as_events(tmp_path: None) -> None:
    """Alert and archive events live in ONE ndjson file."""
    alert_line = next(
        ln for ln in SAMPLE.read_text(encoding="utf-8").splitlines()
        if json.loads(ln)["_index"].startswith("wazuh-alerts")
    )
    event_lines = [
        ln for ln in SAMPLE.read_text(encoding="utf-8").splitlines()
        if json.loads(ln)["_index"].startswith("wazuh-archives")
    ][:5]
    p = _write(tmp_path, [alert_line, *event_lines])
    c = FileConnector(p)
    assert c.get_alert(ALERT_ID).alert_id == ALERT_ID
    assert len(c.search_events({}, datetime(2026, 1, 1, tzinfo=timezone.utc),
                               datetime(2027, 1, 1, tzinfo=timezone.utc))) == 5


# ---------------------------------------------------------------- search_events


FULL_WINDOW = (datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc))


def test_search_events_returns_only_archive_events() -> None:
    events = FileConnector(SAMPLE).search_events({}, *FULL_WINDOW)
    assert all(isinstance(e, Event) for e in events)
    assert all(not e.raw_ref.index.startswith("wazuh-alerts") for e in events)
    assert len(events) == 99


def test_search_events_time_window_filter() -> None:
    start = datetime.fromisoformat("2026-10-31T09:05:00+00:00")
    end = datetime.fromisoformat("2026-10-31T09:10:00+00:00")
    events = FileConnector(SAMPLE).search_events({}, start, end)
    assert events
    for e in events:
        assert start <= e.timestamp < end


def test_search_events_host_filter() -> None:
    events = FileConnector(SAMPLE).search_events({"host": "OTHER-HOST"}, *FULL_WINDOW)
    assert events == []
    events = FileConnector(SAMPLE).search_events({"host": HOST}, *FULL_WINDOW)
    assert len(events) == 97  # 2 decoy events on another host


def test_search_events_field_condition_and_nested_path() -> None:
    events = FileConnector(SAMPLE).search_events(
        {"process.parent.name": "WINWORD.EXE"}, *FULL_WINDOW
    )
    assert len(events) == 1
    # IoC destination appears twice in the kill chain (download + beacon)
    events = FileConnector(SAMPLE).search_events(
        {"destination_ip": "203.0.113.66"}, *FULL_WINDOW
    )
    assert len(events) == 2


def test_search_events_unknown_query_key_raises() -> None:
    with pytest.raises(ConnectorError, match="unsupported query key"):
        FileConnector(SAMPLE).search_events({"no.such.field": "x"}, *FULL_WINDOW)


def test_search_events_limit_applied_after_ordering() -> None:
    all_events = FileConnector(SAMPLE).search_events({}, *FULL_WINDOW)
    limited = FileConnector(SAMPLE).search_events({}, *FULL_WINDOW, limit=10)
    assert limited == all_events[:10]
    assert len(limited) == 10


def test_search_events_utf8_and_escaped_strings() -> None:
    cmd = 'powershell.exe -enc "SGVsbG8" # nhÃ©n vá»‡t \\ "quoted"'
    line = _hit("wazuh-archives-x", "u1",
                {"@timestamp": "2026-10-31T09:00:00Z", "agent": {"name": HOST},
                 "data": {"win": {"eventdata": {"command": cmd}}}})
    p = _write(REPO_ROOT / "tests" / "fixtures" / "ndjson", [line], "utf8-case.ndjson")
    events = FileConnector(p).search_events({}, *FULL_WINDOW)
    assert events[0].command_line == cmd


# ---------------------------------------------------------------- determinism


def test_repeated_reads_identical_and_ordered() -> None:
    a = FileConnector(SAMPLE).search_events({}, *FULL_WINDOW)
    b = FileConnector(SAMPLE).search_events({}, *FULL_WINDOW)
    assert [e.model_dump() for e in a] == [e.model_dump() for e in b]
    assert [e.document_id for e in a] == [e.document_id for e in b]


# ---------------------------------------------------------------- malformed input


def test_malformed_json_reports_file_and_line(tmp_path: None) -> None:
    good = _hit("wazuh-archives-x", "g1", {"@timestamp": "2026-10-31T09:00:00Z",
                                           "agent": {"name": HOST}, "data": {}})
    p = _write(tmp_path, [good, "{not-json"])
    with pytest.raises(ConnectorError) as exc:
        FileConnector(p).search_events({}, *FULL_WINDOW)
    msg = str(exc.value)
    assert p.name in msg and "line 2" in msg


def test_missing_envelope_field_reports_line(tmp_path: None) -> None:
    p = _write(tmp_path, ['{"_index": "i", "_id": "a", "_source": {}}', '{"_id": "x", "_source": {}}'])
    with pytest.raises(ConnectorError, match="line 2.*missing envelope field '_index'"):
        FileConnector(p)


def test_record_missing_timestamp_or_index_raises(tmp_path: None) -> None:
    p = _write(tmp_path, [_hit("wazuh-archives-x", "a", {"agent": {"name": HOST}})])
    with pytest.raises(ConnectorError, match="line 1"):
        FileConnector(p).search_events({}, *FULL_WINDOW)


def test_malformed_input_produces_no_partial_results(tmp_path: None) -> None:
    good = _hit("wazuh-archives-x", "g1", {"@timestamp": "2026-10-31T09:00:00Z",
                                           "agent": {"name": HOST}, "data": {}})
    broken = _write(tmp_path, [good, "broken"], name="broken.ndjson")
    valid = _write(tmp_path, [good], name="valid.ndjson")
    # a connector built over a file that becomes corrupted mid-investigation
    c_ok = FileConnector(valid)
    assert len(c_ok.search_events({}, *FULL_WINDOW)) == 1
    with pytest.raises(ConnectorError):
        FileConnector(broken)  # fail-fast at load: no partial connector exists


def test_nonexistent_file_raises_connector_error(tmp_path: None) -> None:
    with pytest.raises(ConnectorError):
        FileConnector(tmp_path / "missing.ndjson")


# ---------------------------------------------------------------- write_investigation


def test_write_investigation_atomic_and_deterministic(tmp_path: None) -> None:
    report = InvestigationReport.model_validate_json(
        (REPO_ROOT / "tests" / "fixtures" / "ndjson" / "report-minimal.json").read_text(
            encoding="utf-8"
        )
    )
    c = FileConnector(SAMPLE)
    out1 = Path(c.write_investigation(report, output_dir=tmp_path))
    out2 = Path(c.write_investigation(report, output_dir=tmp_path))
    assert out1 == out2 == tmp_path / f"{ALERT_ID}.report.json"
    text = out1.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert not list(tmp_path.glob("*.tmp"))
    assert InvestigationReport.model_validate_json(text) == report
