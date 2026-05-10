"""`trajrl chain` — read-only on-chain queries for any Bittensor subnet."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer

app = typer.Typer(
    name="chain",
    help="Read-only on-chain queries for any Bittensor subnet "
         "(metagraph, emission, hyperparams).",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


_json_opt = typer.Option("--json", "-j", help="Force JSON output (auto when piped).")
_network_opt = typer.Option(
    "--network",
    "-n",
    help="Bittensor network: finney | test | local | archive | ws(s)://endpoint.",
    envvar="BT_NETWORK",
)


def _want_json(flag: bool) -> bool:
    return flag or not sys.stdout.isatty()


def _print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


@app.command()
def metagraph(
    netuid: Annotated[int, typer.Option("--netuid", "-u", help="Subnet UID.")],
    network: Annotated[str, _network_opt] = "finney",
    json_output: Annotated[bool, _json_opt] = False,
) -> None:
    """Dump the metagraph for `netuid`: per-neuron stake, incentive, dividends, trust, consensus."""
    from trajrl.chain.api import get_metagraph
    from trajrl.chain import display as fmt

    data = get_metagraph(netuid=netuid, network=network)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_metagraph(data)


@app.command()
def emission(
    netuid: Annotated[int, typer.Option("--netuid", "-u", help="Subnet UID.")],
    network: Annotated[str, _network_opt] = "finney",
    json_output: Annotated[bool, _json_opt] = False,
) -> None:
    """Show subnet emission, tempo, burn (registration cost) and core hyperparams."""
    from trajrl.chain.api import get_emission
    from trajrl.chain import display as fmt

    data = get_emission(netuid=netuid, network=network)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_emission(data)
