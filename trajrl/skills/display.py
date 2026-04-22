"""Rich formatters for `trajrl skills` TTY output."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


def display_list(payload: dict[str, Any]) -> None:
    skills = payload.get("skills", [])
    if not skills:
        console.print("[yellow]No skills found.[/]")
        return

    table = Table(title=f"Skills ({len(skills)})")
    table.add_column("Slug", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Tags", style="magenta")
    table.add_column("Version", justify="right")
    table.add_column("Updated", justify="right", style="dim")

    for skill in skills:
        tags = skill.get("tags") or []
        table.add_row(
            skill.get("slug", ""),
            skill.get("name", ""),
            ", ".join(tags) if tags else "—",
            skill.get("version") or "—",
            (skill.get("updatedAt") or skill.get("updated_at") or "—")[:19],
        )

    console.print(table)


def display_show(skill: dict[str, Any], *, raw: bool = False) -> None:
    slug = skill.get("slug", "")
    name = skill.get("name", "")
    description = skill.get("description", "")
    tags = skill.get("tags") or []
    version = skill.get("version") or "—"
    agents = skill.get("compatibleAgents") or skill.get("compatible_agents") or []

    header_lines = [
        f"[bold cyan]{name}[/]  [dim]({slug})[/]",
        f"  {description}" if description else "",
        f"  [magenta]tags:[/] {', '.join(tags) if tags else '—'}",
        f"  [magenta]version:[/] {version}",
        f"  [magenta]agents:[/] {', '.join(agents) if agents else '—'}",
    ]
    console.print(Panel("\n".join(line for line in header_lines if line),
                        border_style="cyan", title="skill"))

    content = skill.get("content") or ""
    if raw or not content:
        if content:
            console.print(content)
        return
    console.print(Markdown(content))


def display_install_results(results: list[dict[str, Any]]) -> None:
    if not results:
        console.print("[yellow]No agent targets resolved — nothing installed.[/]")
        return
    table = Table(title=f"Install results ({len(results)})")
    table.add_column("Agent", style="cyan")
    table.add_column("Target")
    table.add_column("Status")
    table.add_column("Reason", style="dim")

    for entry in results:
        table.add_row(
            entry.get("agent", ""),
            entry.get("target", ""),
            entry.get("status", ""),
            entry.get("reason") or "",
        )

    console.print(table)
