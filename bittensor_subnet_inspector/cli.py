"""bittensor-subnet-inspector — generic on-chain query CLI for any Bittensor subnet."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer

from trajrl._version_flag import make_version_callback

app = typer.Typer(
    name="bittensor-subnet-inspector",
    help="Read-only on-chain queries for any Bittensor subnet "
         "(metagraph, emission, hyperparams).",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


@app.callback()
def _main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=make_version_callback("bittensor-subnet-inspector"),
            is_eager=True,
        ),
    ] = False,
) -> None:
    pass


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
    from bittensor_subnet_inspector.api import get_metagraph
    from bittensor_subnet_inspector import display as fmt

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
    from bittensor_subnet_inspector.api import get_emission
    from bittensor_subnet_inspector import display as fmt

    data = get_emission(netuid=netuid, network=network)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_emission(data)
