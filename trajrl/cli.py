"""trajrl — skill hub installer for TrajectoryRL.

Mirrors the npm `trajrl` CLI: discover skills published on trajrl.com and
install them into local agent skill directories (Claude Code, Cursor, Codex,
Hermes, OpenClaw).
"""

from __future__ import annotations

from typing import Annotated

import typer

from trajrl._version_flag import make_version_callback
from trajrl.skills.cli import app as skills_app

app = typer.Typer(
    name="trajrl",
    help="Skill hub installer for TrajectoryRL — browse and install agent skills "
         "optimized by the TrajectoryRL network.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

app.add_typer(skills_app, name="skills")


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=make_version_callback("trajrl"),
            is_eager=True,
        ),
    ] = False,
) -> None:
    pass
