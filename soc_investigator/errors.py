"""Stable exception types and the CLI exit-code mapping (Task 0 contract).

Exit-code table approved via DS-001 (from the execution plan):
    0  success
   10  alert / scenario pack not found
   11  invalid scenario pack
   20  configuration / doctor failure
   30  connector failure
   40  provider failure after retries
   50  verification mismatch
   70  unexpected internal error
Command syntax/usage errors keep Typer's default exit code (2).
"""

from __future__ import annotations

EXIT_OK = 0
EXIT_NOT_FOUND = 10
EXIT_INVALID_PACK = 11
EXIT_CONFIG = 20
EXIT_CONNECTOR = 30
EXIT_PROVIDER = 40
EXIT_VERIFICATION = 50
EXIT_INTERNAL = 70
EXIT_NOT_IMPLEMENTED = EXIT_INTERNAL


class SocInvestigatorError(Exception):
    """Base class for all tool errors. Maps to the internal-error exit code."""

    exit_code = EXIT_INTERNAL


class ScenarioPackNotFound(SocInvestigatorError):
    exit_code = EXIT_NOT_FOUND


class InvalidScenarioPack(SocInvestigatorError):
    exit_code = EXIT_INVALID_PACK


class ConfigError(SocInvestigatorError):
    exit_code = EXIT_CONFIG


class ConnectorError(SocInvestigatorError):
    exit_code = EXIT_CONNECTOR


class ProviderError(SocInvestigatorError):
    exit_code = EXIT_PROVIDER


class VerificationMismatch(SocInvestigatorError):
    exit_code = EXIT_VERIFICATION


def exit_code_for(exc: BaseException) -> int:
    """Return the CLI exit code for an exception instance or type."""
    if isinstance(exc, type):
        target = exc
    else:
        target = type(exc)
    for klass in target.__mro__:
        code = getattr(klass, "exit_code", None)
        if isinstance(code, int):
            return code
    return EXIT_INTERNAL
