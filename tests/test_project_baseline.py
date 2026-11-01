"""Task 0 baseline tests: package metadata, CLI stub, exit-code mapping, config, .gitignore."""

import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]


# --- Package metadata -------------------------------------------------------


def test_package_version_matches_pyproject():
    import soc_investigator

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert soc_investigator.__version__ == data["project"]["version"]


def test_requires_python_312():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert ">=3.12" in data["project"]["requires-python"]


# --- CLI stub ----------------------------------------------------------------


def test_cli_help_exits_zero():
    from soc_investigator.cli import app

    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "command", ["install", "config", "doctor", "investigate", "smoke", "verify", "eval", "export"]
)
def test_stub_commands_exit_70(command):
    """DS-002 (B): all planned commands exist but are not implemented -> exit 70."""
    from soc_investigator.cli import app
    from soc_investigator.errors import EXIT_NOT_IMPLEMENTED

    result = CliRunner().invoke(app, [command])
    assert result.exit_code == EXIT_NOT_IMPLEMENTED
    assert "not implemented" in result.output.lower()


# --- Exit code mapping --------------------------------------------------------

# DS-001 table (per execution plan):
EXPECTED_EXIT_CODES = {
    "ScenarioPackNotFound": 10,
    "InvalidScenarioPack": 11,
    "ConfigError": 20,
    "ConnectorError": 30,
    "ProviderError": 40,
    "VerificationMismatch": 50,
    "SocInvestigatorError": 70,
}


@pytest.mark.parametrize("name,code", sorted(EXPECTED_EXIT_CODES.items()))
def test_exception_maps_to_exit_code(name, code):
    from soc_investigator import errors

    exc_cls = getattr(errors, name)
    assert errors.exit_code_for(exc_cls("x")) == code


def test_exit_code_constants_match_plan_table():
    from soc_investigator import errors

    assert errors.EXIT_OK == 0
    assert errors.EXIT_NOT_FOUND == 10
    assert errors.EXIT_INVALID_PACK == 11
    assert errors.EXIT_CONFIG == 20
    assert errors.EXIT_CONNECTOR == 30
    assert errors.EXIT_PROVIDER == 40
    assert errors.EXIT_VERIFICATION == 50
    assert errors.EXIT_INTERNAL == 70


# --- Config model (DS-003 option A) -------------------------------------------

VALID_CONFIG = {
    "opensearch_url": "https://siem.internal:9200",
    "opensearch_username": "soc-reader",
    "opensearch_password": "secret-not-real",
}


def test_config_accepts_minimal_valid_values_with_defaults():
    from soc_investigator.config import load_config

    cfg = load_config(VALID_CONFIG)
    assert cfg.provider == "ollama"
    assert cfg.model == "qwen2.5:3b-instruct"
    assert cfg.alert_index_pattern == "wazuh-alerts-*"
    assert cfg.archive_index_pattern == "wazuh-archives-*"
    assert cfg.investigation_index_pattern == "ai-investigations-*"
    assert cfg.redact_hostname is False
    assert str(cfg.reports_dir) == "reports"


@pytest.mark.parametrize("missing", sorted(VALID_CONFIG))
def test_config_rejects_missing_required_field(missing):
    from soc_investigator.config import load_config
    from soc_investigator.errors import ConfigError

    payload = dict(VALID_CONFIG)
    del payload[missing]
    with pytest.raises(ConfigError):
        load_config(payload)


def test_config_rejects_invalid_provider():
    from soc_investigator.config import load_config
    from soc_investigator.errors import ConfigError

    with pytest.raises(ConfigError):
        load_config({**VALID_CONFIG, "provider": "openai"})


def test_config_error_message_does_not_leak_secret(monkeypatch):
    """AGENTS.md §7.9: never print secrets."""
    from soc_investigator.config import load_config
    from soc_investigator.errors import ConfigError

    with pytest.raises(ConfigError) as excinfo:
        load_config({**VALID_CONFIG, "opensearch_password": ""})
    assert "secret-not-real" not in str(excinfo.value)


# --- .gitignore ----------------------------------------------------------------


def test_gitignore_protects_env_and_reports():
    lines = {
        line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    assert ".env" in lines
    assert "reports/" in lines
