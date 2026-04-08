# trajrl

The official CLI for [TrajectoryRL](https://github.com/trajectoryRL/trajectoryRL) — an open skill factory that leverages Bittensor's distributed compute and incentive layer with reinforcement learning to produce state-of-the-art agent skills.

One install gives any human or AI agent (Claude Code, Cursor, Codex, OpenClaw, Hermes, Manus, …) access to every skill TrajectoryRL has shipped. Each skill is a self-contained `SKILL.md` that agents can discover and follow directly.

CLI output is JSON when piped, Rich tables when interactive.

## Install

```bash
pip install trajrl
```

## Skills

Skills are the core of `trajrl`. Each one is a self-contained `SKILL.md` providing everything an agent needs: context, CLI commands, and data concepts. The skill catalog is fetched on demand so users always get the latest set as the subnet ships new winners.

### subnet-analyze

Deep analysis of live TrajectoryRL data — validators, submissions, scores, weight distribution, scenarios, and eval logs.

**What an agent can do with this skill:**

```bash
# Full validator analysis — scores, weights, scenarios, leaderboard
trajrl subnet analyze 5FFApaS7...

# Drill into top submissions
trajrl subnet analyze 5FFApaS7... --deep

# Network overview
trajrl subnet status

# JSON output for piping (automatic when piped)
trajrl subnet status | jq '.validators.validators[].hotkey'
```

See [`skills/subnet-analyze/SKILL.md`](skills/subnet-analyze/SKILL.md) for full usage reference.

## Links

- **Subnet repo:** https://github.com/trajectoryRL/trajectoryRL — incentive mechanism, evaluation framework, reference implementation
- **Website:** https://trajrl.com — leaderboard, live subnet data, dashboards
- **Public API spec:** [PUBLIC_API.md](https://github.com/trajectoryRL/trajectoryrl.web/blob/main/PUBLIC_API.md) — read-only, no auth, base URL `https://trajrl.com`
- **Incentive mechanism:** [INCENTIVE_MECHANISM.md](https://github.com/trajectoryRL/trajectoryRL/blob/main/INCENTIVE_MECHANISM.md)
- **Evaluation dataset:** [DATASET_v0.1.md](https://github.com/trajectoryRL/trajectoryRL/blob/main/DATASET_v0.1.md)
