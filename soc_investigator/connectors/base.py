"""SiemConnector protocol (Task 1 contract, verbatim from spec section 7).

Implementations in v0.2: WazuhConnector (live, Task 8) and FileConnector
(NDJSON replay, this task). Pagination in live connectors uses search_after
(sort cursor), never from/size. write_investigation ONLY writes to the tool's
own index/directory — it never mutates source data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from soc_investigator.models import Alert, Event, InvestigationReport


class SiemConnector(Protocol):
    def get_alert(self, alert_id: str) -> Alert: ...

    def search_events(
        self,
        query: dict,
        start: datetime,
        end: datetime,
        limit: int = 500,
    ) -> list[Event]: ...

    def write_investigation(self, report: InvestigationReport) -> str: ...
