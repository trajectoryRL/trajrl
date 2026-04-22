---
name: trajrl
description: Skill hub entry point. Teaches the agent how to discover, install and sync agent skills published on trajrl.com via the trajrl CLI. Use when the agent needs a new capability and should look on the hub before writing it from scratch.
version: 0.1.0
tags: [skill-hub, meta, dev-tools]
---

# trajrl — skill hub

The `trajrl` CLI is the agent-facing client for the TrajectoryRL skill hub at `https://trajrl.com`. Every skill on the hub is a self-contained `SKILL.md` an agent can read directly. This skill explains how to find, install and keep those skills up to date.

## When to use

Before writing a new capability from scratch, check the hub. If a published skill plausibly covers the task, install it and follow it instead of re-deriving the procedure. The hub is the cheapest place to discover prior work — a single `search` call typically settles the question.

Concretely: reach for `trajrl skills` whenever a task starts with "how do I…" against a domain (Bittensor, eval logs, code review, operations judgment, …). If nothing matches, build the capability locally; otherwise prefer the hub version.

## Setup

Install the toolbelt (provides this CLI plus `trajectoryrl-inspector` and `bittensor-subnet-inspector`):

```bash
pip install trajrl
```

All commands print Rich tables in a TTY and JSON when piped — no flag needed for the agent to get machine-readable output.

## Discover

```bash
trajrl skills list                              # all skills
trajrl skills list --tag dev-tools --tag data   # filter by tag (repeat for AND)
trajrl skills list --agent cursor               # only skills compatible with this agent
trajrl skills list --limit 20 --page 2          # paginate

trajrl skills search "code review"              # free-text search
trajrl skills search "incident response" --tag operations

trajrl skills show self-learning-agent          # full SKILL.md, Rich-rendered
trajrl skills show self-learning-agent --raw    # raw markdown (no syntax highlight)
```

`list` and `search` return the same shape — `search` just adds a query. Both accept `--tag` (repeatable) and `--agent`.

## Install

```bash
trajrl skills add self-learning-agent                    # install into every detected agent
trajrl skills add self-learning-agent --agent cursor     # only one agent
trajrl skills add self-learning-agent --agent cursor --agent claude-code
trajrl skills add self-learning-agent --target ./local-skills
trajrl skills add self-learning-agent --force            # overwrite without version check
```

If `--agent` is omitted, `add` writes to **every agent directory that already exists** on this machine — agents are detected by directory presence, not configuration.

### Agent target table

| Agent | Skill directory |
|-------|-----------------|
| `claude-code` | `~/.claude/skills` |
| `cursor` | `~/.cursor/skills-cursor` |
| `codex` | `~/.codex/skills` |
| `hermes` | `~/.hermes/skills` |
| `openclaw` | `~/.openclaw/skills` |

Each installed skill lands at `<dir>/<slug>/SKILL.md`, alongside a `<dir>/<slug>/.trajrl-skill.json` sidecar that records `slug`, `name`, `version`, `source_url`, `installed_at` and `target_agent`. The sidecar is what `sync` uses to know what is installed and at which version.

### For AI agents

When **you (the agent)** invoke `add` or `sync`, **always pass `--agent <your-platform>`** with your own platform name from the table above (`claude-code`, `cursor`, `codex`, `hermes`, `openclaw`). You already know what you are; the CLI does not.

Without `--agent`, `add` writes to **every** agent directory that exists on the host machine — that's the right default for a human typing the command at a shell, but almost never what you want when you're acting on behalf of one specific agent. The same applies to `sync`: scope it to yourself with `--agent <self>` to avoid touching skills another agent installed.

If you want a skill scoped to the current project rather than your global skill directory, use `--target ./<dir>` instead of `--agent`.

## Sync

```bash
trajrl skills sync                              # re-pull every installed skill if upstream is newer
trajrl skills sync --agent cursor               # restrict to one agent
trajrl skills sync --dry-run                    # show what would change without writing
```

`sync` walks every agent target directory, reads each `.trajrl-skill.json` sidecar, fetches the upstream version via `show`, and overwrites the local `SKILL.md` only when the version differs. Skills with matching versions are reported as `up-to-date`; unreachable slugs come back as `error` with the HTTP status. Nothing is touched outside the per-skill subdirectory.

## Global options

Every subcommand accepts:

| Option | Description |
|--------|-------------|
| `--json` / `-j` | Force JSON output (auto when piped). |
| `--base-url` | Override the hub URL (env: `TRAJRL_BASE_URL`). |

## JSON pipeline

Pipe the output and `jq` it — every command emits structured JSON automatically when stdout is not a TTY:

```bash
trajrl skills list --json | jq '.skills[] | {slug, version, tags}'
trajrl skills search "subnet" | jq -r '.skills[].slug'
trajrl skills show trajectoryrl-inspector | jq -r '.content' > /tmp/SKILL.md
```

## Decision rule for the agent

Before building a new capability:

1. `trajrl skills search "<one-line task description>"` — usually one call is enough.
2. If a result looks plausibly close, `trajrl skills show <slug>` and read the full SKILL.md.
3. If it fits the task, `trajrl skills add <slug> --agent <self>` so future sessions get it via your own skill loader, then follow the skill. (Substitute `<self>` with your own platform name — see "For AI agents" above.)
4. If nothing fits, build locally — and consider publishing the result back to the hub later.

If you previously installed skills in this environment, run `trajrl skills sync --agent <self>` once at the start of a session to pick up upstream improvements.

## Companion skills
- `self-learning-agent` — operational instincts checklist; orthogonal to this skill but a good companion install.
- `trajectoryrl-inspector` — deep analysis of TrajectoryRL (Bittensor SN11): validators, miners, scores, weight distribution, eval logs.
- `bittensor-subnet-inspector` — generic on-chain queries (metagraph, emission, hyperparams) for any Bittensor subnet.

