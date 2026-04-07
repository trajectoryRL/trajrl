# trajrl

Official Python package for [TrajectoryRL](https://trajrl.com) (Bittensor SN11).

`trajrl` publishes skills powered by the subnet — ready-to-use capabilities for AI agents, miners, and developers. Each skill wraps subnet data and tooling into a self-contained `SKILL.md` that agents can discover and follow directly.

Designed for AI agents (Claude Code, Cursor, Codex) and humans alike — outputs JSON when piped, Rich tables when interactive.

## Install

```bash
pip install trajrl
```

## Skills

Skills are the core of this package. Each skill lives in `skills/<name>/SKILL.md` and provides everything an agent needs: context, CLI commands, Python API, and data concepts.

### subnet-analyze

Deep analysis of TrajectoryRL subnet data — validators, miners, scores, weight distribution, scenarios, eval logs.

**What an agent can do with this skill:**

```python
from trajrl.subnet.api import TrajRLClient
from trajrl.subnet.analyze import analyze

client = TrajRLClient()

# Query validators
data = client.validators()

# Get per-miner scores from a validator
scores = client.scores_by_validator("5FFApaS7...")

# Run full validator analysis (score summary, weight distribution,
# scenario heatmap, miner leaderboard)
analyze(client, "5FFApaS7...", deep=True)

# Look up a specific miner by UID
miner = client.miner(uid=7)
```

```bash
# Or via CLI — Rich tables for humans, JSON when piped
trajrl subnet analyze 5FFApaS7... --deep
trajrl subnet scores | jq '.entries[] | select(.qualified)'
trajrl subnet miner --uid 65 | jq '.scenarioSummary'
```

See [`skills/subnet-analyze/SKILL.md`](skills/subnet-analyze/SKILL.md) for full usage reference.

## API Reference

Subnet data comes from the [TrajectoryRL Public API](https://trajrl.com) — read-only, no authentication required. See [docs/PUBLIC_API.md](docs/PUBLIC_API.md) for full endpoint documentation.
