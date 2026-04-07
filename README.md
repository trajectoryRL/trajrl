# trajrl

Official Python package for [TrajectoryRL](https://trajrl.com).

`trajrl` publishes skills powered by the subnet — ready-to-use capabilities for AI agents, miners, and developers. Each skill is a self-contained `SKILL.md` that agents can discover and follow directly.

Designed for AI agents (Claude Code, Cursor, Codex) and humans alike — outputs JSON when piped, Rich tables when interactive.

## Install

```bash
pip install trajrl
```

## Skills

Skills are the core of this package. Each skill lives in `skills/<name>/SKILL.md` and provides everything an agent needs: context, CLI commands, and data concepts.

### subnet-analyze

Deep analysis of TrajectoryRL subnet data — validators, miners, scores, weight distribution, scenarios, eval logs.

**What an agent can do with this skill:**

```bash
# Full validator analysis — scores, weights, scenarios, leaderboard
trajrl subnet analyze 5FFApaS7...

# Drill into top miners
trajrl subnet analyze 5FFApaS7... --deep

# Network overview
trajrl subnet status

# JSON output for piping (automatic when piped)
trajrl subnet status | jq '.validators.validators[].hotkey'
```

See [`skills/subnet-analyze/SKILL.md`](skills/subnet-analyze/SKILL.md) for full usage reference.

## API Reference

Subnet data comes from the [TrajectoryRL Public API](https://trajrl.com) — read-only, no authentication required.
