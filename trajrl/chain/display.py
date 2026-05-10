"""Rich formatters for `trajrl chain` TTY output."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _trunc(value: str | None, n: int = 6) -> str:
    if not value:
        return "—"
    if len(value) <= n + 4:
        return value
    return f"{value[:n]}…{value[-4:]}"


def display_metagraph(data: dict[str, Any]) -> None:
    netuid = data.get("netuid")
    network = data.get("network", "—")
    n = data.get("n", 0)
    block = data.get("block")

    title = f"Metagraph netuid={netuid} network={network}"
    if block:
        title += f"  block={block}"
    title += f"  ({n} neurons)"

    table = Table(title=title, show_lines=False)
    table.add_column("UID", justify="right", style="cyan")
    table.add_column("Hotkey")
    table.add_column("Stake", justify="right")
    table.add_column("Incentive", justify="right")
    table.add_column("Dividends", justify="right")
    table.add_column("Trust", justify="right")
    table.add_column("Consensus", justify="right")
    table.add_column("Emission", justify="right")
    table.add_column("VPermit", justify="center")

    for neuron in data.get("neurons", []):
        table.add_row(
            str(neuron.get("uid", "")),
            _trunc(neuron.get("hotkey")),
            f"{neuron.get('stake', 0):.2f}",
            f"{neuron.get('incentive', 0):.4f}",
            f"{neuron.get('dividends', 0):.4f}",
            f"{neuron.get('trust', 0):.4f}",
            f"{neuron.get('consensus', 0):.4f}",
            f"{neuron.get('emission', 0):.6f}",
            "✓" if neuron.get("validator_permit") else "·",
        )

    console.print(table)


def display_emission(data: dict[str, Any]) -> None:
    netuid = data.get("netuid")
    network = data.get("network", "—")

    rows = [
        ("tempo", data.get("tempo")),
        ("emission", data.get("emission")),
        ("burn (TAO)", data.get("burn")),
        ("registration_cost", data.get("registration_cost")),
        ("max_neurons", data.get("max_neurons")),
        ("min_allowed_weights", data.get("min_allowed_weights")),
        ("max_weights_limit", data.get("max_weights_limit")),
        ("weights_rate_limit", data.get("weights_rate_limit")),
        ("immunity_period", data.get("immunity_period")),
        ("activity_cutoff", data.get("activity_cutoff")),
    ]

    body_lines = []
    for key, value in rows:
        rendered = "—" if value is None else str(value)
        body_lines.append(f"  [bold]{key}[/]  {rendered}")

    console.print(
        Panel(
            "\n".join(body_lines),
            title=f"Subnet hyperparams netuid={netuid} network={network}",
            border_style="cyan",
        )
    )
