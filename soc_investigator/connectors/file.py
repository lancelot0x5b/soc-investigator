"""FileConnector — deterministic NDJSON replay (Task 1).

Replay contract (execution plan, Task 1):
- each line is an OpenSearch hit: {"_index": ..., "_id": ..., "_source": {...}};
- records are classified as alerts vs archive events by configured index
  patterns (defaults match the Wazuh deployment in the spec);
- fail-fast on malformed input (DS-009 A): any bad line raises ConnectorError
  naming the file and the 1-based line number; no partial results are ever
  produced or cached;
- repeated reads return identical normalized records in identical order;
- write_investigation atomically persists a report JSON under reports_dir
  (or an explicit output_dir for tests) and returns the path.

The normalizer here is the single place that knows concrete field paths of
the (synthetic, schema-first) fixture envelope. Real Wazuh field mapping must
be confirmed against a genuine export before WazuhConnector (Task 8) — never
guessed from memory.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from soc_investigator.errors import ConnectorError, ScenarioPackNotFound
from soc_investigator.models import Alert, Event, InvestigationReport, RawRef

DEFAULT_ALERT_INDEX_PATTERN = "wazuh-alerts-*"
DEFAULT_ARCHIVE_INDEX_PATTERN = "wazuh-archives-*"

# Normalized Event field -> dotted path inside _source (fixture convention).
_EVENT_FIELD_PATHS: dict[str, tuple[str, ...]] = {
    "event_code": ("data", "win", "eventdata", "event_id"),
    "process_guid": ("data", "win", "eventdata", "process_guid"),
    "parent_process_guid": ("data", "win", "eventdata", "parent_process_guid"),
    "pid": ("data", "win", "eventdata", "process_id"),
    "parent_pid": ("data", "win", "eventdata", "parent_process_id"),
    "image": ("data", "win", "eventdata", "image"),
    "parent_image": ("data", "win", "eventdata", "parent_image"),
    "command_line": ("data", "win", "eventdata", "command"),
    "destination_ip": ("data", "win", "eventdata", "destination_ip"),
    "destination_hostname": ("data", "win", "eventdata", "destination_hostname"),
    "destination_port": ("data", "win", "eventdata", "destination_port"),
    "target_filename": ("data", "win", "eventdata", "target_filename"),
    "file_mtime": ("data", "win", "eventdata", "file_mtime"),
}

# Query keys accepted in search_events(): normalized field names plus aliases.
_QUERY_ALIASES: dict[str, str] = {
    "host": "host",
    "source": "source",
    "process.parent.name": "parent_image",
}


def _matches_pattern(index: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return index.startswith(pattern[:-1])
    if pattern.startswith("*"):
        return index.endswith(pattern[1:])
    return index == pattern


def _dig(source: dict[str, Any], path: tuple[str, ...]) -> Any:
    cur: Any = source
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _parse_ts(value: Any, file_name: str, line_no: int) -> datetime:
    if not isinstance(value, str) or not value:
        raise ConnectorError(
            f"{file_name}: line {line_no}: missing required '@timestamp' in _source"
        )
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        raise ConnectorError(
            f"{file_name}: line {line_no}: invalid '@timestamp' value"
        ) from None
    if dt.tzinfo is None:
        raise ConnectorError(
            f"{file_name}: line {line_no}: '@timestamp' must carry a timezone offset"
        )
    return dt


class FileConnector:
    """Reads one NDJSON file holding both alerts and archive events."""

    def __init__(
        self,
        path: Path,
        *,
        alert_index_pattern: str = DEFAULT_ALERT_INDEX_PATTERN,
        archive_index_pattern: str = DEFAULT_ARCHIVE_INDEX_PATTERN,
    ) -> None:
        self._path = Path(path)
        self._alert_pattern = alert_index_pattern
        self._archive_pattern = archive_index_pattern
        if not self._path.is_file():
            raise ConnectorError(f"replay file not found: {self._path}")
        # Fail fast at construction: parse+normalize every line once, eagerly.
        self._alerts: dict[str, Alert] = {}
        self._events: list[Event] = []
        self._load()

    # ------------------------------------------------------------------ loading

    def _load(self) -> None:
        name = self._path.name
        alerts: dict[str, Alert] = {}
        events: list[Event] = []
        with self._path.open(encoding="utf-8") as fh:
            for line_no, raw_line in enumerate(fh, start=1):
                if not raw_line.strip():
                    continue
                try:
                    rec = json.loads(raw_line)
                except json.JSONDecodeError:
                    raise ConnectorError(
                        f"{name}: line {line_no}: malformed JSON record"
                    ) from None
                if not isinstance(rec, dict):
                    raise ConnectorError(
                        f"{name}: line {line_no}: record is not a JSON object"
                    )
                index, doc_id, source = rec.get("_index"), rec.get("_id"), rec.get("_source")
                for field, value in (("_index", index), ("_id", doc_id)):
                    if not isinstance(value, str) or not value:
                        raise ConnectorError(
                            f"{name}: line {line_no}: missing envelope field '{field}'"
                        )
                if source is None:
                    raise ConnectorError(
                        f"{name}: line {line_no}: missing envelope field '_source'"
                    )
                if not isinstance(source, dict):
                    raise ConnectorError(
                        f"{name}: line {line_no}: '_source' is not a JSON object"
                    )
                ts = _parse_ts(source.get("@timestamp"), name, line_no)
                raw_ref = RawRef(index=index, id=doc_id)
                if _matches_pattern(index, self._alert_pattern):
                    if doc_id in alerts:
                        raise ConnectorError(
                            f"{name}: duplicate alert document id '{doc_id}' "
                            f"(ambiguous replay reference)"
                        )
                    rule = _dig(source, ("rule", "id"))
                    if not isinstance(rule, str) or not rule:
                        raise ConnectorError(
                            f"{name}: line {line_no}: alert record lacks 'rule.id'"
                        )
                    host = _dig(source, ("agent", "name"))
                    user = _dig(source, ("data", "win", "eventdata", "user_name"))
                    alerts[doc_id] = Alert(
                        alert_id=doc_id,
                        rule_id=rule,
                        timestamp=ts,
                        host=host if isinstance(host, str) else None,
                        user=user if isinstance(user, str) else None,
                        raw_ref=raw_ref,
                        raw=source,
                    )
                elif _matches_pattern(index, self._archive_pattern):
                    host = _dig(source, ("agent", "name"))
                    if not isinstance(host, str) or not host:
                        raise ConnectorError(
                            f"{name}: line {line_no}: event record lacks 'agent.name' (host)"
                        )
                    fields: dict[str, Any] = {}
                    for fname, path in _EVENT_FIELD_PATHS.items():
                        val = _dig(source, path)
                        if val is not None:
                            fields[fname] = val
                    events.append(
                        Event(
                            document_id=doc_id,
                            timestamp=ts,
                            host=host,
                            source="sysmon",
                            raw_ref=raw_ref,
                            raw=source,
                            **fields,
                        )
                    )
                # records outside configured patterns are out of scope for replay
        self._alerts = alerts
        self._events = events

    # ------------------------------------------------------------------ queries

    def get_alert(self, alert_id: str) -> Alert:
        try:
            return self._alerts[alert_id]
        except KeyError:
            raise ScenarioPackNotFound(f"alert not found in replay file: {alert_id}") from None

    def search_events(
        self,
        query: dict,
        start: datetime,
        end: datetime,
        limit: int = 500,
    ) -> list[Event]:
        conditions: dict[str, Any] = {}
        for key, value in query.items():
            field = _QUERY_ALIASES.get(key, key)
            if field not in Event.model_fields:
                raise ConnectorError(f"unsupported query key: {key}")
            conditions[field] = value
        selected = [
            e
            for e in self._events  # file order == canonical replay order
            if start <= e.timestamp < end
            and all(getattr(e, f) == v for f, v in conditions.items())
        ]
        return selected[:limit]

    # ------------------------------------------------------------------ writing

    def write_investigation(
        self,
        report: InvestigationReport,
        *,
        output_dir: Path | None = None,
    ) -> str:
        target_dir = Path(output_dir) if output_dir is not None else Path("reports")
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / f"{report.alert_id}.report.json"
        payload = json.dumps(
            json.loads(report.model_dump_json()), indent=2, ensure_ascii=False, sort_keys=True
        ) + "\n"
        tmp = dest.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, dest)
        return str(dest)
