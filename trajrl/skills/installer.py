"""Local agent skill directory installer.

Each known agent platform stores skills in a well-known directory under the
user's home. `add` writes the SKILL.md to every detected agent (or only those
explicitly named via `--agent`); `sync` walks installed skills (identified by
a `.trajrl-skill.json` sidecar) and re-pulls any that have a newer version
upstream.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# -- agent target table ----------------------------------------------------

# Maps agent name → directory template that contains one subdirectory per
# installed skill. The skill itself lives at `<dir>/<slug>/SKILL.md` with a
# sidecar `<dir>/<slug>/.trajrl-skill.json`.
#
# Paths intentionally use `Path.home()` at runtime so tests can monkey-patch.
AGENT_TARGETS: dict[str, str] = {
    "claude-code": "~/.claude/skills",
    "cursor": "~/.cursor/skills-cursor",
    "codex": "~/.codex/skills",
    "hermes": "~/.hermes/skills",
    "openclaw": "~/.openclaw/skills",
}

SIDECAR_NAME = ".trajrl-skill.json"


@dataclass
class InstallResult:
    agent: str
    target: Path
    status: str  # "installed" | "skipped" | "updated" | "missing-dir"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "target": str(self.target),
            "status": self.status,
            "reason": self.reason,
        }


def resolve_target_dir(agent: str) -> Path:
    """Resolve the absolute skill directory for `agent`."""
    template = AGENT_TARGETS.get(agent)
    if template is None:
        raise ValueError(f"Unknown agent: {agent!r}")
    return Path(template).expanduser()


def detect_installed_agents() -> list[str]:
    """Return agents whose top-level skills directory exists on this machine."""
    return [a for a, _ in AGENT_TARGETS.items() if resolve_target_dir(a).exists()]


def install_skill(
    skill: dict[str, Any],
    *,
    agents: Iterable[str] | None = None,
    target_override: Path | None = None,
    force: bool = False,
) -> list[InstallResult]:
    """Write `skill["content"]` into every chosen agent directory.

    Parameters
    ----------
    skill:
        Full skill payload from `SkillsClient.show()` — must contain `slug`
        and `content`. Optional fields (`version`, `download_url`, ...) are
        recorded in the sidecar.
    agents:
        Explicit agent names to install to. If `None`, install to every agent
        whose directory already exists (`detect_installed_agents()`).
    target_override:
        Custom base directory (replaces the agent table for this call). When
        set, exactly one entry is produced labelled `agent="custom"`.
    force:
        Overwrite existing SKILL.md without checking sidecar version.
    """
    slug = skill.get("slug")
    content = skill.get("content")
    if not slug or content is None:
        raise ValueError("skill payload missing 'slug' or 'content'")

    targets: list[tuple[str, Path]] = []
    if target_override is not None:
        targets.append(("custom", Path(target_override).expanduser()))
    else:
        chosen = list(agents) if agents else detect_installed_agents()
        for agent in chosen:
            try:
                targets.append((agent, resolve_target_dir(agent)))
            except ValueError as exc:
                targets.append(
                    (agent, Path("/dev/null"))
                )
                _ = exc  # noqa: F841 — placeholder, recorded below
        # If `agents=` was explicit and a name is unknown, raise so the CLI
        # can surface it cleanly.
        unknown = [a for a in (agents or []) if a not in AGENT_TARGETS]
        if unknown:
            raise ValueError(
                f"Unknown agent(s): {', '.join(unknown)}. "
                f"Known: {', '.join(AGENT_TARGETS)}"
            )

    results: list[InstallResult] = []
    for agent, base_dir in targets:
        skill_dir = base_dir / slug
        skill_path = skill_dir / "SKILL.md"
        sidecar_path = skill_dir / SIDECAR_NAME

        if not base_dir.exists() and target_override is None:
            results.append(
                InstallResult(agent=agent, target=skill_path, status="missing-dir",
                              reason=f"{base_dir} does not exist")
            )
            continue

        existed = skill_path.exists()
        if existed and not force:
            existing_version = _read_sidecar_version(sidecar_path)
            new_version = skill.get("version")
            if existing_version and new_version and existing_version == new_version:
                results.append(
                    InstallResult(agent=agent, target=skill_path, status="skipped",
                                  reason=f"already at version {existing_version}")
                )
                continue

        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(content, encoding="utf-8")
        _write_sidecar(sidecar_path, skill, agent=agent)
        results.append(
            InstallResult(
                agent=agent,
                target=skill_path,
                status="updated" if existed else "installed",
            )
        )

    return results


def list_installed(agents: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Walk every agent target dir and collect installed skills (those with sidecars)."""
    chosen = list(agents) if agents else list(AGENT_TARGETS)
    out: list[dict[str, Any]] = []
    for agent in chosen:
        try:
            base = resolve_target_dir(agent)
        except ValueError:
            continue
        if not base.exists():
            continue
        for sidecar in base.glob(f"*/{SIDECAR_NAME}"):
            try:
                meta = json.loads(sidecar.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            meta["agent"] = agent
            meta["target"] = str(sidecar.parent / "SKILL.md")
            out.append(meta)
    return out


def _write_sidecar(path: Path, skill: dict[str, Any], *, agent: str) -> None:
    payload = {
        "slug": skill.get("slug"),
        "name": skill.get("name"),
        "version": skill.get("version"),
        "source_url": skill.get("download_url") or skill.get("downloadUrl"),
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target_agent": agent,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_sidecar_version(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return meta.get("version")
