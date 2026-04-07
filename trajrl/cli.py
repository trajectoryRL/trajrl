"""trajrl — official skill collection for TrajectoryRL (Bittensor SN11)."""

from __future__ import annotations

from typing import Annotated

import typer

from trajrl.subnet.cli import app as subnet_app

__version__ = "0.3.0"

app = typer.Typer(
    name="trajrl",
    help="Official skill collection for TrajectoryRL (Bittensor SN11).",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

app.add_typer(subnet_app, name="subnet")


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    pass


def _version_callback(value: bool) -> None:
    if value:
        print(f"trajrl version {__version__}")
        raise typer.Exit()
