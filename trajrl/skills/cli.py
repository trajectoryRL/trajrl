"""trajrl skills — list / search / show / add / sync."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import httpx
import typer

from trajrl.skills.api import SkillsClient
from trajrl.skills import display as fmt
from trajrl.skills import installer

app = typer.Typer(
    name="skills",
    help="Browse and install skills from the TrajectoryRL skill hub.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


_json_opt = typer.Option("--json", "-j", help="Force JSON output (auto when piped).")
_base_url_opt = typer.Option(
    "--base-url",
    help="Skill hub base URL.",
    envvar="TRAJRL_BASE_URL",
)


def _client(base_url: str) -> SkillsClient:
    return SkillsClient(base_url=base_url)


def _want_json(flag: bool) -> bool:
    return flag or not sys.stdout.isatty()


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


@app.command("list")
def list_cmd(
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Filter by tag (repeat for AND)."),
    ] = None,
    agent: Annotated[
        str | None,
        typer.Option("--agent", help="Filter by compatible agent."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", "-l", help="Page size."),
    ] = None,
    page: Annotated[
        int | None,
        typer.Option("--page", "-p", help="Page number (1-indexed)."),
    ] = None,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """List available skills."""
    data = _client(base_url).list(tags=tag, agent=agent, limit=limit, page=page)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_list(data)


@app.command("search")
def search_cmd(
    query: Annotated[str, typer.Argument(help="Free-text search query.")],
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Filter by tag (repeat for AND)."),
    ] = None,
    agent: Annotated[
        str | None,
        typer.Option("--agent", help="Filter by compatible agent."),
    ] = None,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Search skills by free-text query."""
    data = _client(base_url).list(query=query, tags=tag, agent=agent)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_list(data)


@app.command("show")
def show_cmd(
    slug: Annotated[str, typer.Argument(help="Skill slug.")],
    raw: Annotated[
        bool,
        typer.Option("--raw", help="Print raw markdown without Rich rendering."),
    ] = False,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Show a single skill (full SKILL.md content)."""
    try:
        data = _client(base_url).show(slug)
    except httpx.HTTPStatusError as exc:
        if _want_json(json_output):
            _print_json({"error": str(exc), "status": exc.response.status_code})
        else:
            fmt.console.print(f"[red]Error fetching {slug}:[/] {exc}")
        raise typer.Exit(1)

    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_show(data, raw=raw)


@app.command("add")
def add_cmd(
    slug: Annotated[str, typer.Argument(help="Skill slug.")],
    agent: Annotated[
        list[str] | None,
        typer.Option(
            "--agent",
            help="Install only to this agent (repeat for multiple). "
                 "If omitted, installs to every detected agent directory.",
        ),
    ] = None,
    target: Annotated[
        Path | None,
        typer.Option(
            "--target",
            help="Custom skills base directory (overrides agent table).",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing skill without version check."),
    ] = False,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Install a skill into local agent skill directories."""
    try:
        data = _client(base_url).show(slug)
    except httpx.HTTPStatusError as exc:
        if _want_json(json_output):
            _print_json({"error": str(exc), "status": exc.response.status_code})
        else:
            fmt.console.print(f"[red]Error fetching {slug}:[/] {exc}")
        raise typer.Exit(1)

    try:
        results = installer.install_skill(
            data, agents=agent, target_override=target, force=force,
        )
    except ValueError as exc:
        if _want_json(json_output):
            _print_json({"error": str(exc)})
        else:
            fmt.console.print(f"[red]{exc}[/]")
        raise typer.Exit(1)

    payload = {
        "slug": slug,
        "version": data.get("version"),
        "results": [r.to_dict() for r in results],
    }
    if _want_json(json_output):
        _print_json(payload)
    else:
        fmt.display_install_results(payload["results"])


@app.command("sync")
def sync_cmd(
    agent: Annotated[
        list[str] | None,
        typer.Option(
            "--agent",
            help="Only sync skills installed for this agent (repeat for multiple).",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would change without writing."),
    ] = False,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Re-pull installed skills from the hub if a newer version is available."""
    installed = installer.list_installed(agents=agent)
    if not installed:
        msg = {"synced": [], "message": "No installed skills found."}
        if _want_json(json_output):
            _print_json(msg)
        else:
            fmt.console.print("[yellow]No installed skills found.[/]")
        return

    client = _client(base_url)
    results: list[dict] = []

    for entry in installed:
        slug = entry.get("slug")
        local_version = entry.get("version")
        target_agent = entry.get("agent")
        if not slug:
            continue
        try:
            remote = client.show(slug)
        except httpx.HTTPStatusError as exc:
            results.append({
                "slug": slug,
                "agent": target_agent,
                "status": "error",
                "reason": f"{exc.response.status_code}",
            })
            continue

        remote_version = remote.get("version")
        if local_version and remote_version and local_version == remote_version:
            results.append({
                "slug": slug,
                "agent": target_agent,
                "status": "up-to-date",
                "version": remote_version,
            })
            continue

        if dry_run:
            results.append({
                "slug": slug,
                "agent": target_agent,
                "status": "would-update",
                "from": local_version,
                "to": remote_version,
            })
            continue

        sub = installer.install_skill(remote, agents=[target_agent], force=True)
        for sr in sub:
            results.append({
                "slug": slug,
                "agent": target_agent,
                "status": "synced" if sr.status in ("installed", "updated") else sr.status,
                "from": local_version,
                "to": remote_version,
                "target": str(sr.target),
            })

    payload = {"synced": results, "dry_run": dry_run}
    if _want_json(json_output):
        _print_json(payload)
    else:
        for entry in results:
            status = entry.get("status")
            slug = entry.get("slug")
            agent_name = entry.get("agent")
            if status == "up-to-date":
                fmt.console.print(f"[dim]{slug} @ {agent_name}: up-to-date[/]")
            elif status in ("synced", "would-update"):
                from_v = entry.get("from") or "?"
                to_v = entry.get("to") or "?"
                fmt.console.print(
                    f"[green]{slug} @ {agent_name}: {status} ({from_v} → {to_v})[/]"
                )
            elif status == "error":
                fmt.console.print(
                    f"[red]{slug} @ {agent_name}: error ({entry.get('reason')})[/]"
                )
            else:
                fmt.console.print(f"{slug} @ {agent_name}: {status}")
