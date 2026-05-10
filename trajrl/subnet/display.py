"""Rich formatters for TTY output."""

from __future__ import annotations

from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# -- helpers ---------------------------------------------------------------


def trunc(hotkey: str | None, n: int = 6) -> str:
    """Truncate a hotkey: 5Cd6ht…sn11"""
    if not hotkey:
        return "—"
    if len(hotkey) <= n + 4:
        return hotkey
    return f"{hotkey[:n]}…{hotkey[-4:]}"


def relative_time(ts: str | None) -> str:
    """ISO/Postgres timestamp → '2h ago'."""
    if not ts:
        return "—"
    try:
        clean = ts.replace("+00", "+00:00").replace(" ", "T")
        if not clean.endswith("Z") and "+" not in clean[10:]:
            clean += "+00:00"
        dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        secs = int(delta.total_seconds())
        if secs < 0:
            return "just now"
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except (ValueError, TypeError):
        return str(ts)


def qual(v: bool | None) -> str:
    if v is None:
        return "—"
    return "[green]\u2713[/]" if v else "[red]\u2717[/]"


def cost(v: float | None) -> str:
    if v is None:
        return "—"
    return f"${v:.4f}"


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def score_fmt(v) -> str:
    f = _to_float(v)
    if f is None:
        return "—"
    return f"{f:.2f}"


def size_fmt(b: int | None) -> str:
    if not b:
        return "—"
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b // 1024}KB"
    return f"{b / (1024 * 1024):.1f}MB"


# -- live state (v6 dual-seat) --------------------------------------------


def display_challenge(data: dict) -> None:
    """Render /api/challenge/state — in-flight epoch snapshot."""
    epoch = data.get("current_epoch") or {}
    submissions = data.get("current_submissions") or []
    cfg = data.get("config") or {}
    block = data.get("current_block")

    head = [
        f"  Epoch: [bold]{epoch.get('id', '—')}[/]  "
        f"({epoch.get('status', '—')})",
        f"  Blocks: {epoch.get('start_block', '—')} → {epoch.get('end_block', '—')}  "
        f"(now {block or '—'})",
        f"  Challenger: {trunc(epoch.get('challenger_hotkey'))}  "
        f"pack {trunc(epoch.get('challenger_pack_hash'), 10)}",
        f"  Quorum: {cfg.get('quorum_fraction', '—')}  "
        f"Margin: {cfg.get('winner_protection_margin', '—')}  "
        f"Cooldown: {cfg.get('miner_cooldown_hours', '—')}h",
    ]
    console.print(Panel("\n".join(head), title="Live Challenge", border_style="cyan"))

    if not submissions:
        console.print("[dim]No validator submissions yet.[/]")
        return

    table = Table(title=f"Validator Submissions ({len(submissions)})")
    table.add_column("Validator", style="cyan")
    table.add_column("Challenger", justify="right")
    table.add_column("Qual", justify="center")
    table.add_column("Winner", justify="right")
    table.add_column("W. Qual", justify="center")
    table.add_column("Reported")
    for s in submissions:
        table.add_row(
            s.get("validator_name") or trunc(s.get("validator_hotkey")),
            score_fmt(s.get("challenger_score")),
            qual(s.get("challenger_qualified")),
            score_fmt(s.get("winner_score")),
            qual(s.get("winner_qualified")),
            relative_time(s.get("created_at")),
        )
    console.print(table)


def display_winner(current_data: dict, history_data: dict, history_n: int) -> None:
    """Render current seated winner + recent change events."""
    w = (current_data or {}).get("winner") or {}
    fin = (current_data or {}).get("finalized_epoch") or {}

    head = [
        f"  Winner: [bold]UID {w.get('uid', '—')}[/] {trunc(w.get('hotkey'))}",
        f"  Pack:   {trunc(w.get('pack_hash'), 10)}  "
        f"score={score_fmt(w.get('score'))}",
        f"  Seated since epoch [bold]{w.get('since_epoch_id', '—')}[/]",
    ]
    if fin:
        head.append(
            f"  Last finalized: epoch {fin.get('challenge_epoch_id', '—')}  "
            f"outcome={fin.get('outcome', '—')}  "
            f"replaced={fin.get('winner_replaced', False)}  "
            f"({relative_time(fin.get('finalized_at'))})"
        )
    console.print(
        Panel("\n".join(head), title="Current Winner (Seated)", border_style="green")
    )

    history = (history_data or {}).get("history") or []
    if history_n > 0:
        history = history[:history_n]
    if not history:
        console.print("[dim]No winner-change events yet.[/]")
        return

    table = Table(title=f"Winner History ({len(history)})")
    table.add_column("Epoch", justify="right")
    table.add_column("UID", justify="right")
    table.add_column("Winner", style="cyan")
    table.add_column("Pack")
    table.add_column("Score", justify="right")
    table.add_column("Changed", justify="center")
    table.add_column("Recorded")
    for h in history:
        table.add_row(
            str(h.get("epoch_id", "—")),
            str(h.get("winner_uid", "—")),
            trunc(h.get("winner_hotkey")),
            trunc(h.get("winner_pack_hash"), 10),
            score_fmt(h.get("winner_score")),
            qual(h.get("changed_from_prev")),
            relative_time(h.get("recorded_at")),
        )
    console.print(table)


def display_queue(data: dict, eligible_only: bool = False) -> None:
    """Render /api/queue — pending eval queue."""
    items = data.get("queue") or []
    if eligible_only:
        items = [q for q in items if q.get("eligible_now")]

    label = "Eligible Now" if eligible_only else "Pending Eval Queue"
    table = Table(title=f"{label} ({len(items)})")
    table.add_column("Submission", style="dim")
    table.add_column("UID", justify="right")
    table.add_column("Miner", style="cyan")
    table.add_column("Pack")
    table.add_column("Eligible", justify="center")
    table.add_column("Submitted")
    for q in items:
        table.add_row(
            str(q.get("submission_id", "—")),
            str(q.get("miner_uid", "—")),
            trunc(q.get("miner_hotkey")),
            trunc(q.get("pack_hash"), 10),
            qual(q.get("eligible_now")),
            relative_time(q.get("submitted_at")),
        )
    console.print(table)


# -- existing surface ------------------------------------------------------


def display_validators(data: dict) -> None:
    valis = data.get("validators", [])
    table = Table(title=f"Validators ({len(valis)})")
    table.add_column("Hotkey", style="cyan")
    table.add_column("UID", justify="right")
    table.add_column("Stake", justify="right")
    table.add_column("Version")
    table.add_column("LLM Model")
    table.add_column("Last Eval")
    table.add_column("Last Seen")
    for v in valis:
        stake = v.get("stake")
        stake_str = f"{int(stake):,}" if isinstance(stake, (int, float)) else "—"
        table.add_row(
            trunc(v.get("hotkey")),
            str(v.get("uid", "—")),
            stake_str,
            v.get("version") or "—",
            v.get("llmModel") or "—",
            relative_time(v.get("lastEvalAt")),
            relative_time(v.get("lastSeen")),
        )
    console.print(table)


def display_validators_detail(data: dict) -> None:
    """Detail view: also shows weightTargets and benchVersion."""
    valis = data.get("validators", [])
    table = Table(title=f"Validators — Detail ({len(valis)})")
    table.add_column("Hotkey", style="cyan")
    table.add_column("UID", justify="right")
    table.add_column("Stake", justify="right")
    table.add_column("Version")
    table.add_column("LLM Model")
    table.add_column("Bench")
    table.add_column("Weights → UIDs")
    table.add_column("Last Eval")
    for v in valis:
        stake = v.get("stake")
        stake_str = f"{int(stake):,}" if isinstance(stake, (int, float)) else "—"
        wt = v.get("weightTargets") or []
        wt_str = ", ".join(str(x) for x in wt) if wt else "—"
        table.add_row(
            trunc(v.get("hotkey")),
            str(v.get("uid", "—")),
            stake_str,
            v.get("version") or "—",
            v.get("llmModel") or "—",
            v.get("benchVersion") or "—",
            wt_str,
            relative_time(v.get("lastEvalAt")),
        )
    console.print(table)


def display_scores(data: dict) -> None:
    entries = data.get("entries", [])
    vali = data.get("validator", "")
    table = Table(title=f"Scores from {trunc(vali)} ({len(entries)} miners)")
    table.add_column("Miner", style="cyan")
    table.add_column("UID", justify="right")
    table.add_column("Qual", justify="center")
    table.add_column("Cost", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Scenarios")
    table.add_column("Rejected")
    for e in entries:
        sc = e.get("scenarioScores") or {}
        passed = sum(1 for s in sc.values() if isinstance(s, dict) and s.get("qualified"))
        total = len(sc)
        sc_str = f"{passed}/{total}" if total else "—"

        rej = ""
        if e.get("rejected"):
            stage = e.get("rejectionStage") or ""
            rej = f"[red]{stage}[/]"

        table.add_row(
            trunc(e.get("minerHotkey")),
            str(e.get("uid") if e.get("uid") is not None else "—"),
            qual(e.get("qualified")),
            cost(e.get("costUsd")),
            score_fmt(e.get("score")),
            score_fmt(e.get("weight")),
            sc_str,
            rej or "—",
        )
    console.print(table)


def display_miner(data: dict) -> None:
    hk = data.get("hotkey", "")
    uid = data.get("uid")
    rank = data.get("rank")

    header_parts = [
        f"Rank: {rank or '—'}",
        f"Qualified: {'yes' if data.get('qualified') else 'no'}",
        f"Cost: {cost(data.get('totalCostUsd'))}",
        f"Score: {score_fmt(data.get('score'))}",
    ]
    detail_parts = [
        f"Confidence: {data.get('confidence', '—')}",
        f"Coverage: {data.get('coverage', '—')}",
        f"Active: {'yes' if data.get('isActive') else 'no'}",
        f"Banned: {'yes' if data.get('isBanned') else 'no'}",
    ]
    pack_parts = [
        f"Pack: {trunc(data.get('packHash'), 10)}",
        f"Winner: {'yes' if data.get('isWinner') else 'no'}",
        f"Bootstrap: {'yes' if data.get('isBootstrap') else 'no'}",
    ]

    lines = [
        "  " + " | ".join(header_parts),
        "  " + " | ".join(detail_parts),
        "  " + " | ".join(pack_parts),
    ]

    ban = data.get("banRecord")
    if ban and ban.get("failedPackCount", 0) > 0:
        lines.append(f"  [red]Ban Record: {ban['failedPackCount']} failed packs[/]")
        for fp in ban.get("failedPacks", [])[:3]:
            reason = (fp.get("reason") or "")[:80]
            lines.append(f"    - {trunc(fp.get('pack_hash'), 10)}: {reason}…")

    console.print(
        Panel(
            "\n".join(lines),
            title=f"Miner {trunc(hk)} (UID {uid or '—'})",
            border_style="cyan",
        )
    )

    scenarios = data.get("scenarioSummary", [])
    if scenarios:
        st = Table(title="Scenario Summary")
        st.add_column("Name")
        st.add_column("Avg Cost", justify="right")
        st.add_column("Avg Score", justify="right")
        st.add_column("Qualified")
        st.add_column("Validators", justify="right")
        for s in scenarios:
            st.add_row(
                s.get("name", "—"),
                cost(s.get("avgCost")),
                score_fmt(s.get("avgScore")),
                f"{s.get('qualCount', 0)}/{s.get('validatorCount', 0)}",
                str(s.get("validatorCount", "—")),
            )
        console.print(st)

    validators = data.get("validators", [])
    if validators:
        vt = Table(title="Validator Reports")
        vt.add_column("Validator", style="cyan")
        vt.add_column("Qual", justify="center")
        vt.add_column("Cost", justify="right")
        vt.add_column("Score", justify="right")
        vt.add_column("Block", justify="right")
        vt.add_column("Reported")
        vt.add_column("Rejected")
        for v in validators:
            rej = ""
            if v.get("rejected"):
                rej = f"[red]{v.get('rejectionStage', '')}[/]"
            vt.add_row(
                trunc(v.get("hotkey")),
                qual(v.get("qualified")),
                cost(v.get("costUsd")),
                score_fmt(v.get("score")),
                str(v.get("blockHeight") or "—"),
                relative_time(v.get("createdAt")),
                rej or "—",
            )
        console.print(vt)

    subs = data.get("recentSubmissions", [])
    if subs:
        st2 = Table(title="Recent Submissions")
        st2.add_column("Pack Hash", style="cyan")
        st2.add_column("Status")
        st2.add_column("Reason")
        st2.add_column("Submitted")
        for s in subs:
            status = s.get("evalStatus", "—")
            style = "green" if status == "passed" else "red"
            reason = (s.get("evalReason") or "—")[:60]
            st2.add_row(
                trunc(s.get("packHash"), 10),
                f"[{style}]{status}[/]",
                reason,
                relative_time(s.get("submittedAt")),
            )
        console.print(st2)


def display_pack(data: dict) -> None:
    ph = data.get("packHash", "")
    summary = data.get("summary", {})

    lines = [
        f"  Status: {data.get('evalStatus', '—')}",
        f"  Miner: {trunc(data.get('minerHotkey'))} (UID {data.get('minerUid', '—')})",
        f"  Qualified: {qual(summary.get('qualified'))}  ({summary.get('qualifiedCount', 0)}/{summary.get('validatorCount', 0)} validators)",
        f"  Best Cost: {cost(summary.get('bestCost'))}  |  Avg Cost: {cost(summary.get('avgCost'))}",
    ]
    if data.get("evalReason"):
        lines.append(f"  [red]Reason: {data['evalReason']}[/]")

    console.print(Panel("\n".join(lines), title=f"Pack {trunc(ph, 10)}", border_style="cyan"))

    validators = data.get("validators", [])
    if validators:
        for v in validators:
            vt = Table(title=f"Validator {trunc(v.get('hotkey'))}")
            vt.add_column("Scenario")
            vt.add_column("Cost", justify="right")
            vt.add_column("Score", justify="right")
            vt.add_column("Qualified", justify="center")
            for sc in v.get("scenarios", []):
                vt.add_row(
                    sc.get("name", "—"),
                    cost(sc.get("cost")),
                    score_fmt(sc.get("score")),
                    qual(sc.get("qualified")),
                )
            console.print(vt)


def display_submissions(data: dict, failed_only: bool = False) -> None:
    subs = data.get("submissions", [])
    if failed_only:
        subs = [s for s in subs if s.get("evalStatus") == "failed"]

    label = "Failed Submissions" if failed_only else f"Submissions ({len(subs)})"
    table = Table(title=label)
    table.add_column("Miner", style="cyan")
    table.add_column("Pack Hash", style="cyan")
    table.add_column("Status")
    table.add_column("Reason", max_width=50)
    table.add_column("Submitted")
    for s in subs:
        status = s.get("evalStatus", "—")
        style = "green" if status == "passed" else "red"
        table.add_row(
            trunc(s.get("minerHotkey")),
            trunc(s.get("packHash"), 10),
            f"[{style}]{status}[/]",
            (s.get("evalReason") or "—")[:50],
            relative_time(s.get("submittedAt")),
        )
    console.print(table)


def display_cycle_log(data: dict) -> None:
    """Show cycle log metadata and raw text content."""
    log_entry = data.get("log_entry", {})
    text = data.get("text", "")

    lines = [
        f"  Eval ID: [bold]{log_entry.get('evalId', '—')}[/]",
        f"  Validator: [cyan]{trunc(log_entry.get('validatorHotkey'))}[/]",
        f"  Block: {log_entry.get('blockHeight', '—')}",
        f"  Size: {size_fmt(log_entry.get('sizeBytes'))}",
        f"  Created: {relative_time(log_entry.get('createdAt'))}",
    ]
    console.print(Panel("\n".join(lines), title="Cycle Log", border_style="cyan"))
    console.print(text)


def display_miner_log(log_entry: dict, archive_bytes: bytes) -> None:
    """Display a miner log archive (S1: SKILL.md + JUDGE.md + per-episode files)."""
    import json

    from trajrl.subnet.api import (
        extract_archive_file,
        list_archive_members,
    )

    lines = [
        f"  Eval ID: [bold]{log_entry.get('evalId', '—')}[/]",
        f"  Validator: [cyan]{trunc(log_entry.get('validatorHotkey'))}[/]",
        f"  Miner:     [cyan]{trunc(log_entry.get('minerHotkey'))}[/] "
        f"(uid {log_entry.get('minerUid', '—')})",
        f"  Pack:      {trunc(log_entry.get('packHash'), 10)}",
        f"  Block:     {log_entry.get('blockHeight', '—')}",
        f"  Size:      {size_fmt(log_entry.get('sizeBytes'))}",
        f"  Created:   {relative_time(log_entry.get('createdAt'))}",
    ]
    console.print(Panel("\n".join(lines), title="Miner Eval Log",
                        border_style="cyan"))

    members = list_archive_members(archive_bytes)
    if members:
        tree_table = Table(title="Archive Contents", show_header=True)
        tree_table.add_column("File")
        tree_table.add_column("Size", justify="right")
        for name, size in members:
            tree_table.add_row(name, size_fmt(size))
        console.print(tree_table)

    meta_text = extract_archive_file(archive_bytes, "metadata.json")
    if meta_text:
        try:
            meta = json.loads(meta_text)
            summary = [
                f"  Scenario:     [bold]{meta.get('scenario', '—')}[/]",
                f"  Final score:  [bold green]{meta.get('final_score', 0):.4f}[/]",
                f"  Mean quality: {meta.get('mean_quality', 0):.4f}",
                f"  Delta:        {meta.get('delta', 0):.4f}  "
                f"(bonus {meta.get('learning_bonus', 0):.4f})",
                f"  Episodes:     {meta.get('episode_qualities', [])}",
            ]
            console.print(Panel("\n".join(summary), title="Eval Summary",
                                border_style="green"))
        except Exception:
            pass

    n_episodes = sum(
        1 for name, _ in members
        if name.startswith("episodes/episode_") and name.endswith("/evaluation.json")
    )
    if n_episodes:
        crit_table = Table(title=f"Per-Episode Criteria ({n_episodes} episodes)")
        crit_table.add_column("Episode", justify="right")
        crit_table.add_column("Quality", justify="right")
        eval_data = []
        for i in range(n_episodes):
            eval_text = extract_archive_file(
                archive_bytes, f"episodes/episode_{i}/evaluation.json")
            if eval_text:
                try:
                    eval_data.append(json.loads(eval_text))
                except Exception:
                    eval_data.append({})
            else:
                eval_data.append({})
        criteria_names = set()
        for ed in eval_data:
            criteria_names.update((ed.get("criteria") or {}).keys())
        for name in sorted(criteria_names):
            crit_table.add_column(name[:8], justify="right")
        for i, ed in enumerate(eval_data):
            row = [str(i), f"{ed.get('quality', 0):.2f}"]
            crits = ed.get("criteria") or {}
            for name in sorted(criteria_names):
                v = crits.get(name)
                row.append(f"{v:.2f}" if isinstance(v, (int, float)) else "—")
            crit_table.add_row(*row)
        console.print(crit_table)


def display_logs(data: dict) -> None:
    logs = data.get("logs", [])
    table = Table(title=f"Eval Logs ({len(logs)})")
    table.add_column("Eval ID")
    table.add_column("Type")
    table.add_column("Validator", style="cyan")
    table.add_column("Miner", style="cyan")
    table.add_column("Pack Hash")
    table.add_column("Size", justify="right")
    table.add_column("GCS URL", max_width=50)
    table.add_column("Created")
    for log in logs:
        table.add_row(
            log.get("evalId", "—"),
            log.get("logType", "—"),
            trunc(log.get("validatorHotkey")),
            trunc(log.get("minerHotkey")),
            trunc(log.get("packHash"), 10),
            size_fmt(log.get("sizeBytes")),
            (log.get("gcsUrl") or "—")[-50:],
            relative_time(log.get("createdAt")),
        )
    console.print(table)
