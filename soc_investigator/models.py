"""Normalized domain contracts (Task 1, DS-008 option A: full definitions now).

Field names and shapes follow the spec verbatim:
- section 7 / execution plan Task 1 for Alert/Event/RawRef/Evidence/EvidenceBundle;
- section 9 for InvestigationReport;
- investigation-ledger structure for InvestigationLedger.

Only ``document_id``, ``timestamp``, ``host``, ``raw_ref`` and ``raw`` are
required on Event — telemetry may legitimately lack the rest.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "0.2.6"


class RawRef(BaseModel):
    """Pointer back to the original document in the SIEM index."""

    model_config = ConfigDict(extra="forbid")

    index: str
    id: str


class Alert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str
    rule_id: str
    timestamp: datetime
    host: str | None = None
    user: str | None = None
    raw_ref: RawRef
    raw: dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    timestamp: datetime
    host: str
    source: str
    event_code: int | str | None = None
    process_guid: str | None = None
    parent_process_guid: str | None = None
    pid: int | None = None
    parent_pid: int | None = None
    image: str | None = None
    parent_image: str | None = None
    command_line: str | None = None
    destination_ip: str | None = None
    destination_hostname: str | None = None
    destination_port: int | None = None
    target_filename: str | None = None
    file_mtime: datetime | None = None
    raw_ref: RawRef
    raw: dict[str, Any] = Field(default_factory=dict)


EvidenceType = Literal["process_create", "network", "file_change"]


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    type: EvidenceType
    timestamp: datetime
    summary: str
    raw_ref: RawRef


class BundleAlertMeta(BaseModel):
    """Warning metadata inside an EvidenceBundle (spec section 8)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    rule: str
    timestamp: datetime
    host: str | None = None
    user: str | None = None


class IocEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    value: str
    first_seen: str | None = None  # evidence_id where first observed


class BudgetDropStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)


class BundleStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_events: int
    distilled_evidence: int
    per_type_counts: dict[str, int] = Field(default_factory=dict)
    dropped_by_budget: BudgetDropStats = Field(default_factory=BudgetDropStats)


class EvidenceBundle(BaseModel):
    """Correlator output — the only thing a model ever sees (spec section 8)."""

    model_config = ConfigDict(extra="forbid")

    alert: BundleAlertMeta
    scenario_id: str
    evidence: list[Evidence] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)  # ordered evidence ids
    iocs: list[IocEntry] = Field(default_factory=list)
    stats: BundleStats


# ------------------------------------------------------------------ report parts


class ReportModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    name: str


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str
    citations: list[str] = Field(default_factory=list)


class TimelineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    event: str
    citations: list[str] = Field(default_factory=list)


class ReportIoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    value: str
    citations: list[str] = Field(default_factory=list)


class AttackMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technique_id: str
    name: str
    confidence: Literal["high", "medium", "low"]
    citations: list[str] = Field(default_factory=list)


ChecklistStatus = Literal["confirmed", "refuted", "inconclusive"]


class ChecklistResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    tier: Literal["A", "B", "C"]
    question: str
    status: ChecklistStatus
    citations: list[str] = Field(default_factory=list)
    reason: str | None = None  # required when inconclusive (validator's job)


PlaybookStepStatus = Literal["answered", "unanswered", "out_of_scope"]


class PlaybookResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: str
    status: PlaybookStepStatus
    reason: str | None = None  # required when unanswered/out_of_scope


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str
    based_on: list[str] = Field(default_factory=list)  # evidence ids
    confidence: Literal["high", "medium", "low"]


class EvidenceState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    per_type_counts: dict[str, int] = Field(default_factory=dict)
    abnormal_absences: list[Any] = Field(default_factory=list)
    declared_blind: list[str] = Field(default_factory=list)


class PlaybookFileProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str
    sha256: str


class PlaybookProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[PlaybookFileProvenance] = Field(default_factory=list)


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    priority: str
    would_enable: str | None = None
    source: str | None = None  # e.g. "playbook" — replaces citations there


class RedactionMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    counts: dict[str, int] = Field(default_factory=dict)


class ValidationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dropped_claims: int = 0
    unverified_claims: int = 0


class BudgetMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applied: bool = False
    dropped_evidence: int = 0
    dropped_types: dict[str, int] = Field(default_factory=dict)


class EvidenceStatsMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_events: int
    distilled_evidence: int


class ReportMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["live", "replay"]
    ledger_file: str
    redaction: RedactionMeta
    validation: ValidationMeta = Field(default_factory=ValidationMeta)
    budget: BudgetMeta = Field(default_factory=BudgetMeta)
    latency_ms: int | None = None
    evidence_stats: EvidenceStatsMeta


class SnapshotEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    sha256: str
    raw: dict[str, Any]


class EvidenceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_sha256: str
    events: list[SnapshotEvent] = Field(default_factory=list)


class InvestigationReport(BaseModel):
    """Section 9 contract — changing a field name breaks verify/eval/dashboard."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    alert_id: str
    scenario_id: str
    generated_at: datetime
    model: ReportModelInfo
    summary: str
    facts: list[Fact] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)
    iocs: list[ReportIoc] = Field(default_factory=list)
    attack_mapping: list[AttackMapping] = Field(default_factory=list)
    checklist_results: list[ChecklistResult] = Field(default_factory=list)
    playbook_results: list[PlaybookResult] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    scope_statement: str
    evidence_state: EvidenceState
    playbook_provenance: PlaybookProvenance
    recommendations: list[Recommendation] = Field(default_factory=list)
    meta: ReportMeta
    evidence_snapshot: EvidenceSnapshot


# ------------------------------------------------------------------ ledger part


class LedgerPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    pack_sha256: str | None = None


class LedgerAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt: int
    error: str | None = None


class LedgerValidatorAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    detail: str | None = None


class InvestigationLedger(BaseModel):
    """reports/<alert_id>.ledger.json — 'conversation memory' (spec section 9)."""

    model_config = ConfigDict(extra="forbid")

    alert_id: str
    pack: LedgerPack
    prompt_redacted: str
    report_draft: dict[str, Any]
    attempts: list[LedgerAttempt] = Field(default_factory=list)
    validator_actions: list[LedgerValidatorAction] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)
    timings_ms: dict[str, int] = Field(default_factory=dict)
