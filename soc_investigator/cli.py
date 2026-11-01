"""Typer CLI entry point `soc-investigator` (Task 0 stub, DS-002 option B).

All planned commands are registered but print "not implemented" and exit with
code 70 until their owning task (Task 2–10) builds them. Syntax/usage errors
keep Typer's default exit code (2).
"""

from __future__ import annotations

import typer

from soc_investigator import __version__
from soc_investigator.errors import EXIT_NOT_IMPLEMENTED

app = typer.Typer(
    name="soc-investigator",
    help="SOC Investigator — deterministic evidence-first SIEM investigation assistant.",
    no_args_is_help=True,
)

# Commands per spec v0.2.6; each is owned by a later task in the execution plan.
_COMMANDS = (
    "install",
    "config",
    "doctor",
    "investigate",
    "smoke",
    "verify",
    "eval",
    "export",
)


def _make_stub(name: str):
    def stub() -> None:
        typer.echo(f"'{name}' is not implemented yet (planned in a later task).")
        raise typer.Exit(code=EXIT_NOT_IMPLEMENTED)

    stub.__name__ = name
    stub.__doc__ = f"[not implemented] {name} command."
    return stub


for _name in _COMMANDS:
    app.command(name=_name)(_make_stub(_name))


@app.callback(invoke_without_command=False)
def main(version: bool = typer.Option(False, "--version", help="Show version and exit.")) -> None:
    if version:
        typer.echo(f"soc-investigator {__version__}")
        raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
