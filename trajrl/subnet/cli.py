"""trajrl subnet — query live TrajectoryRL subnet data."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer

from trajrl.subnet.api import TrajRLClient
from trajrl.subnet import display as fmt
from trajrl.subnet import analyze as _analyze

app = typer.Typer(
    name="subnet",
    help="Query live validator, miner, and evaluation data from the TrajectoryRL subnet.",
    no_args_is_help=True,
)

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


# -- commands --------------------------------------------------------------

@app.command()
def status(
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Network health overview — validators, submissions, models."""
    client = _client(base_url)
    vali_data = client.validators()
    subs_data = client.submissions()
    if _want_json(json_output):
        _print_json({"validators": vali_data, "submissions": subs_data})
    else:
        fmt.display_status(vali_data, subs_data)


@app.command()
def download(
    hotkey: Annotated[str | None, typer.Argument(help="Miner SS58 hotkey.")] = None,
    pack_hash: Annotated[str | None, typer.Argument(help="Pack SHA-256 hash (default: current pack).")] = None,
    uid: Annotated[int | None, typer.Option("--uid", "-u", help="Miner UID (alternative to hotkey)")] = None,
    json_output: Annotated[bool, _json_opt] = False,
    base_url: Annotated[str, _base_url_opt] = "https://trajrl.com",
) -> None:
    """Download a miner's pack and its evaluation results."""
    client = _client(base_url)
    if hotkey is None and uid is not None:
        miner_data = _resolve_miner(client, None, uid)
        hotkey = miner_data["hotkey"]
        if pack_hash is None:
            pack_hash = miner_data.get("packHash")
    elif hotkey is not None and pack_hash is None:
        miner_data = _resolve_miner(client, hotkey, None)
        pack_hash = miner_data.get("packHash")

    if not hotkey or not pack_hash:
        raise typer.BadParameter("Provide miner hotkey or --uid")

    data = client.pack(hotkey, pack_hash)
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
    """Full validator analysis: scores, weight distribution, scenario breakdown, miner leaderboard."""
    client = _client(base_url)
    hotkey = _resolve_validator(client, validator, uid) if (validator or uid is not None) else None
    if hotkey is None:
        hotkey = _analyze.pick_validator_interactive(client)
        if not hotkey:
            raise typer.Exit()
    _analyze.analyze(client, hotkey, deep=deep, deep_n=deep_n, show_logs=show_logs, dump=dump)


@app.command()
def logs(
    validator: Annotated[str | None, typer.Option("--validator", "-v",
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

    # --show or --dump-to: fetch the actual archive
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

        # --show: type-aware pretty print
        if entry.get("logType") == "cycle":
            text = extract_cycle_log(archive) or ""
            if _want_json(json_output):
                _print_json({"log_entry": entry, "text": text})
            else:
                fmt.display_cycle_log({"log_entry": entry, "text": text})
        else:
            if _want_json(json_output):
                # In JSON mode, list members + metadata (not raw bytes)
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

    # Otherwise: list metadata
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
