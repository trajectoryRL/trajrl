"""trajrl — official Python CLI for TrajectoryRL (Bittensor SN11).

One binary, two groups:

- ``trajrl skills ...`` — skill hub (browse + install agent skills)
- ``trajrl <subnet command>`` — live SN11 state (challenge, winner, queue,
  validators, miner, pack, submissions, analyze, logs)

For generic Bittensor on-chain queries (metagraph, hyperparams), use
``btcli`` — the official Bittensor CLI.
"""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer

from trajrl._version_flag import make_version_callback
from trajrl.skills.cli import app as skills_app
from trajrl.subnet.api import TrajRLClient
from trajrl.subnet import display as fmt
from trajrl.subnet import analyze as _analyze

app = typer.Typer(
    name="trajrl",
    help="Official CLI for TrajectoryRL (Bittensor SN11). Browse skills, "
         "watch live subnet state, analyze validators.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


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


# Sub-groups
app.add_typer(skills_app, name="skills")


# -- shared option defaults ------------------------------------------------

_json_opt = typer.Option("--json", "-j", help="Force JSON output (auto when piped).")
_base_url_opt = typer.Option("--base-url", help="API base URL.", envvar="TRAJRL_BASE_URL")


def _client(base_url: str) -> TrajRLClient:
    return TrajRLClient(base_url=base_url)


def _want_json(flag: bool) -> bool:
    return flag or not sys.stdout.isatty()


def _print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _resolve_validator(client: TrajRLClient, hotkey: str | None, uid: int | None) -> str:
    """Resolve a validator hotkey from hotkey or UID. Returns first active if both are None."""
    if hotkey:
        return hotkey
    validators_data = client.validators()
    valis = validators_data.get("validators", [])
    if uid is not None:
        for v in valis:
            if v.get("uid") == uid:
                return v["hotkey"]
        raise typer.BadParameter(f"No validator with UID {uid}")
    if valis:
        return valis[0]["hotkey"]
    raise typer.BadParameter("No active validators found")


def _resolve_miner(client: TrajRLClient, hotkey: str | None, uid: int | None) -> dict:
    """Resolve miner data from hotkey or UID. Returns full miner dict."""
    if hotkey is None and uid is None:
        raise typer.BadParameter("Provide miner hotkey or --uid")
    return client.miner(hotkey=hotkey, uid=uid)


# -- live state (v6 dual-seat) --------------------------------------------


@app.command()
def challenge(
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """In-flight epoch snapshot — challenger pack + per-validator scores so far."""
    data = _client(base_url).challenge_state()
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_challenge(data)


@app.command()
def winner(
    history: Annotated[int, typer.Option(
        "--history",
        help="How many recent winner-change events to show (0 to hide history).",
    )] = 5,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Current seated winner; also prints recent change events (--history N)."""
    client = _client(base_url)
    current = client.winner_current()
    history_data = client.winner_history(limit=history) if history > 0 else {"history": []}
    if _want_json(json_output):
        _print_json({"current": current, "history": history_data})
    else:
        fmt.display_winner(current, history_data, history)


@app.command()
def queue(
    limit: Annotated[int | None, typer.Option(
        "--limit", "-l", help="Max queue items to show.",
    )] = None,
    eligible_only: Annotated[bool, typer.Option(
        "--eligible-only", help="Only include submissions eligible right now.",
    )] = False,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Pending eval queue — what's waiting to be picked up by a validator."""
    data = _client(base_url).queue(limit=limit)
    if eligible_only:
        data = {**data, "queue": [q for q in data.get("queue", []) if q.get("eligible_now")]}
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_queue(data, eligible_only=eligible_only)


# -- validators / miners / packs ------------------------------------------


@app.command()
def validators(
    detail: Annotated[bool, typer.Option(
        "--detail", help="Show stake, weightTargets, benchVersion (wider table).",
    )] = False,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Validator roster — version, model, last eval, last seen."""
    data = _client(base_url).validators()
    if _want_json(json_output):
        _print_json(data)
    else:
        if detail:
            fmt.display_validators_detail(data)
        else:
            fmt.display_validators(data)


@app.command()
def miner(
    hotkey: Annotated[str | None, typer.Argument(help="Miner SS58 hotkey.")] = None,
    uid: Annotated[int | None, typer.Option(
        "--uid", "-u", help="Miner UID (alternative to hotkey).",
    )] = None,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Miner detail — current pack, score, validator reports, recent submissions."""
    if hotkey is None and uid is None:
        raise typer.BadParameter("Provide miner hotkey or --uid")
    data = _resolve_miner(_client(base_url), hotkey, uid)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_miner(data)


@app.command()
def pack(
    hotkey: Annotated[str, typer.Argument(help="Miner SS58 hotkey.")],
    pack_hash: Annotated[str, typer.Argument(help="Pack SHA-256 hash.")],
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Download a specific pack and its evaluation results."""
    data = _client(base_url).pack(hotkey, pack_hash)
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_pack(data)


@app.command()
def submissions(
    failed: Annotated[bool, typer.Option("--failed", help="Show only failed submissions.")] = False,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Recent pack submissions (passed and failed)."""
    data = _client(base_url).submissions()
    if failed:
        data["submissions"] = [s for s in data.get("submissions", []) if s.get("evalStatus") == "failed"]
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_submissions(data, failed_only=failed)


@app.command()
def analyze(
    validator: Annotated[str | None, typer.Argument(help="Validator SS58 hotkey (interactive if omitted).")] = None,
    uid: Annotated[int | None, typer.Option("--uid", "-u", help="Validator UID (alternative to hotkey).")] = None,
    deep: Annotated[bool, typer.Option("--deep", help="Drill into top miners.")] = False,
    deep_n: Annotated[int, typer.Option("--deep-n", help="Number of miners to drill into with --deep.")] = 5,
    show_logs: Annotated[bool, typer.Option("--logs", help="Show recent eval logs.")] = False,
    dump: Annotated[bool, typer.Option("--dump", help="Dump raw JSON to file.")] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Validator deep-dive: scores, weight distribution, scenario heatmap, leaderboard."""
    client = _client(base_url)
    hotkey = _resolve_validator(client, validator, uid) if (validator or uid is not None) else None
    if hotkey is None:
        hotkey = _analyze.pick_validator_interactive(client)
        if not hotkey:
            raise typer.Exit()
    _analyze.analyze(client, hotkey, deep=deep, deep_n=deep_n, show_logs=show_logs, dump=dump)


@app.command()
def logs(
    validator: Annotated[str | None, typer.Option("--validator", "-V",
        help="Filter by validator SS58 hotkey.")] = None,
    miner: Annotated[str | None, typer.Option("--miner", "-m",
        help="Filter by miner SS58 hotkey.")] = None,
    log_type: Annotated[str | None, typer.Option("--type", "-t",
        help="Log type: 'miner' (per-miner eval archive) or 'cycle' "
             "(validator cycle log). Omit for any.")] = None,
    eval_id: Annotated[str | None, typer.Option("--eval-id",
        help="Filter by eval cycle ID.")] = None,
    pack_hash: Annotated[str | None, typer.Option("--pack-hash",
        help="Filter by pack hash.")] = None,
    limit: Annotated[int, typer.Option("--limit", "-l",
        help="Max results when listing.")] = 50,
    show: Annotated[bool, typer.Option("--show", "-s",
        help="Download and display the latest matching log.")] = False,
    dump_to: Annotated[str | None, typer.Option("--dump-to",
        help="Extract the latest matching archive to this directory. "
             "Implies --show semantics (takes the top match).")] = None,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """List or view evaluation log archives.

    - Without --show or --dump-to: lists matching archive metadata.
    - With --show: downloads latest match; cycle logs print validator.log,
      miner logs print archive contents + per-episode criteria.
    - With --dump-to DIR: extracts the archive to DIR for local inspection.
    """
    from trajrl.subnet.api import extract_cycle_log, extract_archive_to_dir

    client = _client(base_url)

    if show or dump_to:
        try:
            result = client.log_archive(
                validator=validator, miner=miner, log_type=log_type,
                eval_id=eval_id, pack_hash=pack_hash,
            )
        except ValueError as e:
            if _want_json(json_output):
                _print_json({"error": str(e)})
            else:
                fmt.console.print(f"[yellow]{e}[/]")
            raise typer.Exit(1)

        entry = result["log_entry"]
        archive = result["archive"]

        if dump_to:
            extract_archive_to_dir(archive, dump_to)
            msg = {"extracted_to": dump_to, "log_entry": entry}
            if _want_json(json_output):
                _print_json(msg)
            else:
                fmt.console.print(
                    f"[green]Extracted to[/] [bold]{dump_to}[/]")
                fmt.console.print(
                    f"  Eval ID: {entry.get('evalId', '—')}  "
                    f"Type: {entry.get('logType', '—')}  "
                    f"Size: {fmt.size_fmt(entry.get('sizeBytes'))}")
            return

        if entry.get("logType") == "cycle":
            text = extract_cycle_log(archive) or ""
            if _want_json(json_output):
                _print_json({"log_entry": entry, "text": text})
            else:
                fmt.display_cycle_log({"log_entry": entry, "text": text})
        else:
            if _want_json(json_output):
                from trajrl.subnet.api import (
                    list_archive_members, extract_archive_file,
                )
                members = list_archive_members(archive)
                meta_text = extract_archive_file(archive, "metadata.json")
                _print_json({
                    "log_entry": entry,
                    "members": [{"name": n, "size": s} for n, s in members],
                    "metadata": json.loads(meta_text) if meta_text else None,
                })
            else:
                fmt.display_miner_log(entry, archive)
        return

    data = client.eval_logs(
        validator=validator,
        miner=miner,
        log_type=log_type,
        eval_id=eval_id,
        pack_hash=pack_hash,
        limit=limit,
    )
    if _want_json(json_output):
        _print_json(data)
    else:
        fmt.display_logs(data)
