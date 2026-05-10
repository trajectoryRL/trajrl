"""Subnet-level analyze: network throughput, competition health, score distribution,
per-scenario breakdown, validator sync, recent winner changes.

v2.2.0 reshape: under v6 winner-challenger, validators all evaluate the same
challenger each epoch. Per-validator leaderboards from v5 don't translate; the
useful unit is the network's eval pipeline as a whole.

Data sources (all read-only HTTP):
- /api/challenge/state — current epoch + config
- /api/epoch/{id} — per-epoch full detail (submissions + scenario results)
- /api/winner/history — winner-change events
- /api/v2/winner/current — currently seated winner
- /api/stats — network totals
"""

from __future__ import annotations

import statistics
from concurrent.futures import ThreadPoolExecutor

from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from trajrl.subnet.api import TrajRLClient
from trajrl.subnet.display import (
    console,
    trunc,
    relative_time,
    score_fmt,
    qual,
)
from rich.table import Table


# Approximate finney block time (seconds). Used only to translate --last 24h
# into an epoch count; if the chain block time changes this is harmless drift.
_BLOCK_TIME_SECS = 12.0


def analyze(
    client: TrajRLClient,
    *,
    last_hours: float | None = 24.0,
    epochs: int | None = None,
    scenario: str | None = None,
    deep: bool = False,
    no_compare: bool = False,
) -> None:
    """Subnet-level network analysis over a window of recent epochs."""
    state = client.challenge_state()
    cfg = state.get("config") or {}
    cur_epoch = int((state.get("current_epoch") or {}).get("id", 0))
    epoch_blocks = int(cfg.get("epoch_length_blocks", 150))

    if epochs is not None:
        n_epochs = max(1, int(epochs))
    else:
        secs = (last_hours or 24.0) * 3600
        n_epochs = max(1, int(secs / (epoch_blocks * _BLOCK_TIME_SECS)))

    # Pull the previous N finalized epochs (skip current — likely in_progress)
    epoch_ids = list(range(max(1, cur_epoch - n_epochs), cur_epoch))
    if not epoch_ids:
        console.print("[yellow]No finalized epochs in window.[/]")
        return

    console.rule(
        f"[bold]Subnet Analysis — last {n_epochs} epochs (≈{n_epochs * epoch_blocks * _BLOCK_TIME_SECS / 3600:.1f}h)[/]"
    )

    epoch_data = _fetch_epochs_parallel(client, epoch_ids)
    epochs_with_data = [e for e in epoch_data if e and e.get("epoch")]
    if not epochs_with_data:
        console.print("[yellow]No epoch data returned. The endpoint may be down.[/]")
        return

    history = client.winner_history(limit=50).get("history") or []
    current_winner = (client.winner_current() or {}).get("winner") or {}
    stats = {}
    try:
        stats = client.stats() or {}
    except Exception:
        pass

    if scenario:
        console.print(f"[dim]Filter: scenario = [bold]{scenario}[/][/]\n")

    _print_throughput(epochs_with_data, n_epochs)
    _print_competition_health(epochs_with_data, history, current_winner, cur_epoch)
    _print_score_distribution(epochs_with_data)
    _print_per_scenario(epochs_with_data, scenario_filter=scenario)
    _print_top_challengers(epochs_with_data)
    _print_rejection_breakdown(epochs_with_data)
    _print_miner_pool(epochs_with_data)
    if not no_compare:
        _print_validator_sync(epochs_with_data)
    _print_recent_winner_changes(history, n=10)
    _print_stats_footer(stats)

    if deep:
        _drill_into_logs(client, epochs_with_data)


# -- fetching --------------------------------------------------------------


def _fetch_epochs_parallel(client: TrajRLClient, epoch_ids: list[int]) -> list[dict]:
    """Fetch epoch detail in parallel with a Rich progress bar."""
    results: list[dict] = [None] * len(epoch_ids)  # type: ignore[list-item]

    def _fetch(i_id: tuple[int, int]) -> tuple[int, dict | None]:
        i, ep_id = i_id
        try:
            return i, client.epoch(ep_id)
        except Exception:
            return i, None

    with Progress(
        SpinnerColumn(),
        TextColumn("[dim]Fetching epoch detail[/]"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        transient=True,
    ) as prog:
        task = prog.add_task("epochs", total=len(epoch_ids))
        with ThreadPoolExecutor(max_workers=8) as ex:
            for i, data in ex.map(_fetch, list(enumerate(epoch_ids))):
                results[i] = data  # type: ignore[assignment]
                prog.advance(task)

    return [r for r in results if r is not None]


# -- sub-reports -----------------------------------------------------------


def _print_throughput(epochs: list[dict], window_size: int) -> None:
    finalized = [e for e in epochs if (e["epoch"] or {}).get("status") == "finalized"]
    in_progress = [e for e in epochs if (e["epoch"] or {}).get("status") == "in_progress"]
    total_subs = sum(len(e.get("submissions") or []) for e in epochs)
    rejected_subs = 0
    validators = set()
    for e in epochs:
        for s in e.get("submissions") or []:
            validators.add(s.get("validator_hotkey"))
            ch = s.get("challenger") or {}
            if ch.get("rejected"):
                rejected_subs += 1

    hours = window_size * 150 * _BLOCK_TIME_SECS / 3600  # approx
    rej_rate = rejected_subs / total_subs * 100 if total_subs else 0

    lines = [
        f"  Epochs in window: {len(epochs)} ({len(finalized)} finalized, {len(in_progress)} in_progress)",
        f"  Decisions submitted: [bold]{total_subs}[/] ({total_subs / hours:.1f}/h)",
        f"  Validators contributing: {len(validators)}",
        f"  Rejection rate: [{'red' if rej_rate > 30 else 'yellow' if rej_rate > 10 else 'green'}]"
        f"{rej_rate:.1f}%[/]  ({rejected_subs}/{total_subs})",
    ]
    console.print(Panel("\n".join(lines), title="Throughput", border_style="cyan"))


def _print_competition_health(
    epochs: list[dict], history: list[dict], current_winner: dict, cur_epoch: int
) -> None:
    finalized = [e for e in epochs if (e["epoch"] or {}).get("status") == "finalized"]
    distinct_packs = {(e["epoch"] or {}).get("challenger_pack_hash") for e in finalized}
    distinct_packs.discard(None)
    distinct_miners = {(e["epoch"] or {}).get("challenger_hotkey") for e in finalized}
    distinct_miners.discard(None)

    outcomes: dict[str, int] = {}
    for e in finalized:
        out = (e["epoch"] or {}).get("outcome") or "unknown"
        outcomes[out] = outcomes.get(out, 0) + 1
    held = outcomes.get("winner_held", 0)
    replaced = outcomes.get("winner_replaced", 0)
    decided = held + replaced
    replace_rate = replaced / decided * 100 if decided else 0

    distinct_winners = {h.get("winner_hotkey") for h in history}
    distinct_winners.discard(None)

    since = current_winner.get("since_epoch_id")
    tenure = (cur_epoch - int(since)) if since else None

    # Mean inter-replacement gap from history (epoch deltas between consecutive changes)
    epoch_changes = sorted(
        {int(h["epoch_id"]) for h in history if h.get("changed_from_prev")}
    )
    if len(epoch_changes) >= 2:
        gaps = [
            epoch_changes[i + 1] - epoch_changes[i]
            for i in range(len(epoch_changes) - 1)
        ]
        mean_gap = statistics.mean(gaps)
    else:
        mean_gap = None

    lines = [
        f"  Distinct challenger packs: [bold]{len(distinct_packs)}[/]  miners: [bold]{len(distinct_miners)}[/]",
        f"  Outcomes: [green]{held} held[/]  [yellow]{replaced} replaced[/]  "
        f"replace_rate=[{'green' if replace_rate < 10 else 'yellow' if replace_rate < 30 else 'red'}]{replace_rate:.1f}%[/]",
        f"  Distinct winners (history+current): [bold]{len(distinct_winners) + (1 if current_winner.get('hotkey') and current_winner.get('hotkey') not in distinct_winners else 0)}[/]",
        f"  Current winner tenure: [bold]{tenure if tenure is not None else '?'} epochs[/]"
        + (f"  ({trunc(current_winner.get('hotkey'))} UID {current_winner.get('uid','?')})" if current_winner else ""),
        f"  Mean inter-replacement gap: {f'{mean_gap:.1f} epochs' if mean_gap is not None else 'n/a (need ≥2 changes)'}",
    ]
    console.print(Panel("\n".join(lines), title="Competition Health", border_style="cyan"))


def _print_score_distribution(epochs: list[dict]) -> None:
    scores = []
    for e in epochs:
        ep = e.get("epoch") or {}
        if ep.get("status") != "finalized":
            continue
        s = ep.get("consensus_score")
        try:
            scores.append(float(s))
        except (TypeError, ValueError):
            pass

    if not scores:
        return

    scores_sorted = sorted(scores)
    p = lambda q: scores_sorted[min(len(scores_sorted) - 1, int(q * (len(scores_sorted) - 1)))]
    mean = statistics.mean(scores)
    qualified = sum(1 for s in scores if s > 0)

    # 5-bucket histogram
    buckets = [(0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 99.0)]
    counts = [
        sum(1 for s in scores if lo <= s < hi)
        for lo, hi in buckets
    ]
    max_c = max(counts) or 1

    lines = [
        f"  N: {len(scores)}  Qualified (>0): {qualified} ({qualified/len(scores)*100:.0f}%)",
        f"  Mean: {mean:.3f}  p50: {p(0.5):.3f}  p75: {p(0.75):.3f}  p90: {p(0.9):.3f}  p99: {p(0.99):.3f}",
        "",
        "  Histogram (consensus_score):",
    ]
    for (lo, hi), c in zip(buckets, counts):
        bar_len = int(c / max_c * 30)
        bar = "[cyan]" + "█" * bar_len + "[/]" + "·" * (30 - bar_len)
        label = f"{lo:.1f}–{hi:.1f}" if hi < 99 else f"{lo:.1f}+"
        lines.append(f"  {label:>9}  {bar}  {c}")
    console.print(Panel("\n".join(lines), title="Score Distribution", border_style="cyan"))


def _print_per_scenario(epochs: list[dict], scenario_filter: str | None = None) -> None:
    """Aggregate per-scenario stats across all submissions in the window."""
    sc_stats: dict[str, dict] = {}
    for e in epochs:
        for s in e.get("submissions") or []:
            sr = (s.get("challenger") or {}).get("scenario_results") or {}
            for name, info in sr.items():
                if scenario_filter and name != scenario_filter:
                    continue
                if not isinstance(info, dict):
                    continue
                d = sc_stats.setdefault(
                    name, {"evals": 0, "qualified": 0, "scores": [], "best_pack": None, "best_score": -1.0}
                )
                d["evals"] += 1
                if info.get("qualified"):
                    d["qualified"] += 1
                sc = info.get("score")
                try:
                    sc_f = float(sc)
                    d["scores"].append(sc_f)
                    if sc_f > d["best_score"]:
                        d["best_score"] = sc_f
                        d["best_pack"] = (e["epoch"] or {}).get("challenger_pack_hash")
                except (TypeError, ValueError):
                    pass

    if not sc_stats:
        if scenario_filter:
            console.print(
                f"[yellow]No data for scenario '{scenario_filter}' in this window.[/]"
            )
        return

    title = (
        f"Per-Scenario — {scenario_filter}"
        if scenario_filter
        else f"Per-Scenario ({len(sc_stats)} scenarios)"
    )
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Scenario")
    table.add_column("Evals", justify="right")
    table.add_column("Pass Rate", justify="right")
    table.add_column("Mean Score", justify="right")
    table.add_column("Best Pack")
    table.add_column("Best Score", justify="right")
    for name, d in sorted(sc_stats.items()):
        rate = d["qualified"] / d["evals"] * 100 if d["evals"] else 0
        rate_style = "green" if rate >= 50 else "yellow" if rate >= 25 else "red"
        mean_s = statistics.mean(d["scores"]) if d["scores"] else 0
        table.add_row(
            name,
            str(d["evals"]),
            f"[{rate_style}]{rate:.0f}%[/] ({d['qualified']}/{d['evals']})",
            f"{mean_s:.3f}",
            trunc(d["best_pack"], 10) if d["best_pack"] else "—",
            f"{d['best_score']:.3f}" if d["best_score"] >= 0 else "—",
        )
    console.print(table)


def _print_top_challengers(epochs: list[dict], top_n: int = 10) -> None:
    by_pack: dict[str, dict] = {}
    for e in epochs:
        ep = e.get("epoch") or {}
        ph = ep.get("challenger_pack_hash")
        if not ph:
            continue
        try:
            score = float(ep.get("consensus_score") or 0)
        except (TypeError, ValueError):
            score = 0
        existing = by_pack.get(ph)
        if existing is None or score > existing["score"]:
            by_pack[ph] = {
                "score": score,
                "miner_hotkey": ep.get("challenger_hotkey"),
                "outcome": ep.get("outcome"),
                "epoch_id": ep.get("id"),
                "qualified": ep.get("consensus_qualified"),
            }

    ranked = sorted(by_pack.items(), key=lambda kv: kv[1]["score"], reverse=True)[:top_n]
    if not ranked:
        return

    table = Table(title=f"Top {len(ranked)} Challenger Packs (by best consensus_score)", box=box.ROUNDED)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Pack", style="cyan")
    table.add_column("Miner")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Qual", justify="center")
    table.add_column("Outcome")
    table.add_column("Epoch", justify="right")
    for i, (ph, d) in enumerate(ranked, 1):
        outcome = d["outcome"] or "—"
        out_style = "yellow" if outcome == "winner_replaced" else "dim"
        table.add_row(
            str(i),
            trunc(ph, 10),
            trunc(d["miner_hotkey"]),
            f"{d['score']:.3f}",
            qual(d["qualified"]),
            f"[{out_style}]{outcome}[/]",
            str(d["epoch_id"]),
        )
    console.print(table)


def _print_rejection_breakdown(epochs: list[dict]) -> None:
    rejections: list[tuple[str, str | None]] = []
    for e in epochs:
        for s in e.get("submissions") or []:
            ch = s.get("challenger") or {}
            if ch.get("rejected"):
                rejections.append((s.get("validator_hotkey", ""), ch.get("rejection_detail")))

    if not rejections:
        return

    by_validator: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    sample_by_reason: dict[str, str] = {}
    for vh, detail in rejections:
        by_validator[vh] = by_validator.get(vh, 0) + 1
        bucket = _bucket_rejection(detail)
        by_reason[bucket] = by_reason.get(bucket, 0) + 1
        if bucket not in sample_by_reason and detail:
            sample_by_reason[bucket] = detail[:80]

    table = Table(title=f"Rejection Breakdown ({len(rejections)} total)", box=box.SIMPLE_HEAVY)
    table.add_column("Reason", style="red")
    table.add_column("Count", justify="right")
    table.add_column("Sample detail", style="dim")
    for reason, cnt in sorted(by_reason.items(), key=lambda kv: -kv[1]):
        table.add_row(reason, str(cnt), sample_by_reason.get(reason, "—"))
    console.print(table)


def _bucket_rejection(detail: str | None) -> str:
    """Coarse-grained reason classifier from rejection_detail text."""
    if not detail:
        return "unspecified"
    d = detail.lower()
    if "copy" in d or "owned by" in d:
        return "integrity:copy"
    if "schema" in d:
        return "schema_validation"
    if "timeout" in d:
        return "timeout"
    if "fetch" in d or "download" in d or "404" in d:
        return "pack_fetch"
    if "size" in d:
        return "pack_size"
    if "eval_error" in d or "eval error" in d:
        return "eval_error"
    if "judge" in d:
        return "judge_failure"
    return "other"


def _print_miner_pool(epochs: list[dict]) -> None:
    distinct_miners: dict[str, int] = {}
    distinct_packs_per_miner: dict[str, set] = {}
    for e in epochs:
        ep = e.get("epoch") or {}
        mh = ep.get("challenger_hotkey")
        ph = ep.get("challenger_pack_hash")
        if mh:
            distinct_miners[mh] = distinct_miners.get(mh, 0) + 1
        if mh and ph:
            distinct_packs_per_miner.setdefault(mh, set()).add(ph)

    if not distinct_miners:
        return

    top = sorted(distinct_miners.items(), key=lambda kv: -kv[1])[:10]
    lines = [
        f"  Distinct miners challenging: [bold]{len(distinct_miners)}[/]",
        f"  Distinct packs across pool:  [bold]{sum(len(v) for v in distinct_packs_per_miner.values())}[/]",
        f"  Mean packs per miner:        {sum(len(v) for v in distinct_packs_per_miner.values()) / len(distinct_packs_per_miner):.1f}",
        "",
        "  Top 10 most-active miners:",
    ]
    for mh, cnt in top:
        lines.append(
            f"    {trunc(mh)}  {cnt} attempts  ({len(distinct_packs_per_miner.get(mh, set()))} distinct packs)"
        )
    console.print(Panel("\n".join(lines), title="Miner Pool", border_style="cyan"))


def _print_validator_sync(epochs: list[dict]) -> None:
    """For each validator, compute mean |my_score - peer_mean| across shared epochs."""
    finalized = [e for e in epochs if (e["epoch"] or {}).get("status") == "finalized"]
    deltas: dict[str, list[float]] = {}
    decisions: dict[str, int] = {}
    rejection_count: dict[str, int] = {}

    for e in finalized:
        subs = e.get("submissions") or []
        if len(subs) < 2:
            continue
        # gather (validator → score) for this epoch
        scores_this_epoch: dict[str, float] = {}
        for s in subs:
            vh = s.get("validator_hotkey")
            ch = s.get("challenger") or {}
            decisions[vh] = decisions.get(vh, 0) + 1
            if ch.get("rejected"):
                rejection_count[vh] = rejection_count.get(vh, 0) + 1
            try:
                scores_this_epoch[vh] = float(ch.get("score") or 0)
            except (TypeError, ValueError):
                continue
        # for each validator, compute |their_score - mean_of_peers|
        for vh, my_score in scores_this_epoch.items():
            peers = [v for k, v in scores_this_epoch.items() if k != vh]
            if not peers:
                continue
            peer_mean = sum(peers) / len(peers)
            deltas.setdefault(vh, []).append(abs(my_score - peer_mean))

    if not deltas:
        return

    # Outlier = mean Δ exceeds 1.5× the network median Δ. Adapts to overall variance.
    all_means = [statistics.mean(ds) for ds in deltas.values()]
    network_median = statistics.median(all_means) if all_means else 0
    threshold = max(0.3, network_median * 1.5)

    table = Table(
        title=f"Validator Sync (vs peer mean) — outlier threshold Δ > {threshold:.2f}",
        box=box.ROUNDED,
    )
    table.add_column("Validator", style="cyan")
    table.add_column("Decisions", justify="right")
    table.add_column("Rejected", justify="right")
    table.add_column("Mean Δ", justify="right")
    table.add_column("Status", justify="center")
    for vh, ds in sorted(deltas.items(), key=lambda kv: -statistics.mean(kv[1])):
        mean_d = statistics.mean(ds)
        is_outlier = mean_d > threshold
        table.add_row(
            trunc(vh),
            str(decisions.get(vh, 0)),
            str(rejection_count.get(vh, 0)),
            f"{mean_d:.3f}",
            "[red]outlier[/]" if is_outlier else "[green]ok[/]",
        )
    console.print(table)


def _print_recent_winner_changes(history: list[dict], n: int = 10) -> None:
    if not history:
        return
    table = Table(title=f"Recent Winner Changes (last {min(n, len(history))})", box=box.SIMPLE)
    table.add_column("Epoch", justify="right")
    table.add_column("UID", justify="right")
    table.add_column("Winner", style="cyan")
    table.add_column("Pack")
    table.add_column("Score", justify="right")
    table.add_column("Recorded")
    for h in history[:n]:
        table.add_row(
            str(h.get("epoch_id", "—")),
            str(h.get("winner_uid", "—")),
            trunc(h.get("winner_hotkey")),
            trunc(h.get("winner_pack_hash"), 10),
            score_fmt(h.get("winner_score")),
            relative_time(h.get("recorded_at")),
        )
    console.print(table)


def _print_stats_footer(stats: dict) -> None:
    if not stats:
        return
    parts = []
    if stats.get("totalReports"):
        parts.append(f"reports={stats['totalReports']}")
    if stats.get("totalCostUsd") is not None:
        parts.append(f"cost=${float(stats['totalCostUsd']):,.2f}")
    if stats.get("totalLlmCalls"):
        parts.append(f"llm_calls={stats['totalLlmCalls']}")
    if stats.get("totalTokens"):
        parts.append(f"tokens={int(stats['totalTokens']):,}")
    if parts:
        console.print(f"[dim]Network totals (all-time): {'  '.join(parts)}[/]")


def _drill_into_logs(client: TrajRLClient, epochs: list[dict], top_n: int = 3) -> None:
    """For --deep: list eval logs for the top-scoring challenger packs in the window."""
    by_pack: dict[str, dict] = {}
    for e in epochs:
        ep = e.get("epoch") or {}
        ph = ep.get("challenger_pack_hash")
        if not ph:
            continue
        try:
            score = float(ep.get("consensus_score") or 0)
        except (TypeError, ValueError):
            score = 0
        if ph not in by_pack or score > by_pack[ph]["score"]:
            by_pack[ph] = {"score": score, "epoch_id": ep.get("id")}

    top = sorted(by_pack.items(), key=lambda kv: -kv[1]["score"])[:top_n]
    if not top:
        return

    console.rule(f"[bold]--deep: eval logs for top {len(top)} packs[/]")
    for ph, info in top:
        console.print(f"\n[cyan]Pack[/] {ph[:16]}…  best_score={info['score']:.3f}  epoch={info['epoch_id']}")
        try:
            logs_data = client.eval_logs(pack_hash=ph, limit=3)
        except Exception as exc:
            console.print(f"  [red]eval_logs fetch failed: {exc}[/]")
            continue
        logs = logs_data.get("logs") or []
        if not logs:
            console.print("  [dim]No eval logs for this pack.[/]")
            continue
        for log in logs:
            console.print(
                f"  • {log.get('logType','?'):<6}  "
                f"{trunc(log.get('validatorHotkey'))}  "
                f"eval_id={log.get('evalId','?')}  "
                f"{relative_time(log.get('createdAt'))}"
            )
