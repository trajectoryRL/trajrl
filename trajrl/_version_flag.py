"""Shared ``--version`` flag helper for all three CLI binaries.

Usage in a Typer app::

    from trajrl._version_flag import make_version_callback

    @app.callback()
    def main(
        version: Annotated[bool, typer.Option(
            "--version", "-v", help="Show version and exit.",
            callback=make_version_callback("trajrl"), is_eager=True,
        )] = False,
    ) -> None:
        pass
"""

from __future__ import annotations

from typing import Callable

import typer

from trajrl import __version__


def make_version_callback(binary_name: str) -> Callable[[bool], None]:
    """Build a Typer eager-callback that prints ``<binary_name> version X``."""

    def _callback(value: bool) -> None:
        if value:
            print(f"{binary_name} version {__version__}")
            raise typer.Exit()

    return _callback
