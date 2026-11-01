"""Compact configuration model (Task 0, DS-003 option A).

Loaded from a plain dict (e.g. parsed YAML/env in later tasks). No plugin or
provider discovery framework — validation only. Invalid/missing required
values raise ConfigError, which maps to CLI exit code 20.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError, field_validator

from soc_investigator.errors import ConfigError

DEFAULT_MODEL = "qwen2.5:3b-instruct"


class Config(BaseModel):
    opensearch_url: str
    opensearch_username: str
    opensearch_password: str
    provider: Literal["ollama", "anthropic"] = "ollama"
    model: str = DEFAULT_MODEL
    alert_index_pattern: str = "wazuh-alerts-*"
    archive_index_pattern: str = "wazuh-archives-*"
    investigation_index_pattern: str = "ai-investigations-*"
    redact_hostname: bool = False
    reports_dir: Path = Path("reports")

    @field_validator("opensearch_url", "opensearch_username", "opensearch_password", "model")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-empty string")
        return value


def load_config(data: dict[str, Any]) -> Config:
    """Validate a raw mapping into a Config; raise ConfigError on failure."""
    try:
        return Config.model_validate(data)
    except ValidationError as exc:
        # Re-render without values so secrets never reach the terminal/log.
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()
        )
        raise ConfigError(f"invalid configuration — {problems}") from None
