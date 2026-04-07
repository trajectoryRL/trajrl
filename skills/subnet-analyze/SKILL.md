---
name: subnet-analyze
description: Query and analyze TrajectoryRL subnet (SN11) data — validators, miners, scores, weights, scenarios, eval logs. Use when the user asks about subnet status, validator analysis, miner performance, weight distribution, or wants to run trajrl CLI commands.
---

# Subnet Analyze

Analyze TrajectoryRL subnet data via the `trajrl` CLI or the Python API directly.

## CLI Usage

Entry point: `trajrl subnet <command>`

### Quick Commands

```bash
trajrl subnet status                    # network overview
trajrl subnet validators               # list all validators
trajrl subnet scores [HOTKEY]           # per-miner scores from a validator
trajrl subnet miner HOTKEY              # miner detail
trajrl subnet miner --uid 7             # miner by UID
trajrl subnet download HOTKEY [HASH]    # pack evaluation data
trajrl subnet submissions               # recent submissions
trajrl subnet submissions --failed      # failed submissions only
trajrl subnet logs                       # eval log archives
trajrl subnet logs --show               # download & display latest cycle log
```

### Full Analyzer

```bash
trajrl subnet analyze [HOTKEY]          # interactive validator picker if omitted
trajrl subnet analyze --uid 5           # by validator UID
trajrl subnet analyze HOTKEY --deep     # drill into top miners
trajrl subnet analyze HOTKEY --deep-n 10
trajrl subnet analyze HOTKEY --logs     # include eval logs
trajrl subnet analyze HOTKEY --dump     # dump raw JSON to file
```

### Global Options

| Option | Description |
|--------|-------------|
| `--json` / `-j` | Force JSON output (auto when piped) |
| `--base-url` | Override API base URL (env: `TRAJRL_BASE_URL`) |

## Python API

### TrajRLClient

```python
from trajrl.subnet.api import TrajRLClient

client = TrajRLClient()  # default: https://trajrl.com
```

Key methods:

| Method | Returns |
|--------|---------|
| `client.validators()` | `{"validators": [...]}` |
| `client.scores_by_validator(hotkey)` | `{"entries": [...]}` |
| `client.scores_by_validator(uid=5)` | resolve UID → hotkey, then fetch |
| `client.miner(hotkey)` | full miner detail dict |
| `client.miner(uid=7)` | resolve UID → hotkey, then fetch |
| `client.pack(hotkey, pack_hash)` | pack evaluation data |
| `client.submissions()` | `{"submissions": [...]}` |
| `client.eval_logs(validator=..., miner=..., log_type=..., eval_id=..., limit=...)` | `{"logs": [...]}` |
| `client.cycle_log(validator)` | `{"log_entry": {...}, "text": "..."}` — downloads & extracts cycle log |

### Analyze Module

```python
from trajrl.subnet.analyze import analyze, pick_validator_interactive
from trajrl.subnet.api import TrajRLClient

client = TrajRLClient()

# Interactive: list validators, prompt user to pick
hotkey = pick_validator_interactive(client)

# Run full analysis (prints rich tables to console)
analyze(client, hotkey)
analyze(client, hotkey, deep=True, deep_n=10)
analyze(client, hotkey, show_logs=True)
analyze(client, hotkey, dump=True)  # saves JSON to file
```

The `analyze()` function produces:
1. **Score Summary** — miners evaluated, qualification rate, cost/score stats
2. **Rejection Breakdown** — counts by rejection stage
3. **Weight Distribution** — parsed from cycle log, shows per-miner weights, gate status, winner
4. **Scenario Heatmap** — pass rate, avg cost/score per scenario
5. **Top 15 Leaderboard** — miners ranked by score
6. With `--deep`: per-miner drill-down (rank, validators, submissions)

### Display Module

Formatting helpers in `trajrl.subnet.display`:

| Function | Purpose |
|----------|---------|
| `trunc(hotkey, n=6)` | `"5Cd6ht…sn11"` |
| `relative_time(iso_ts)` | `"2h ago"` |
| `qual(bool)` | green ✓ / red ✗ / — |
| `cost(float)` | `"$8.4200"` |
| `score_fmt(float)` | `"0.95"` |

## API Endpoints Reference

For full API field definitions, see [docs/PUBLIC_API.md](../../docs/PUBLIC_API.md).

| Endpoint | Description |
|----------|-------------|
| `GET /api/validators` | All validators with heartbeat, version, LLM model |
| `GET /api/scores/by-validator?validator=HOTKEY` | Per-miner scores from a validator |
| `GET /api/miners/:hotkey` | Miner detail: rank, scenarios, validators, submissions, ban record |
| `GET /api/miners/:hotkey/packs/:hash` | Pack evaluation breakdown |
| `GET /api/submissions` | Recent 100 submissions |
| `GET /api/eval-logs` | Eval log archives (type=miner or type=cycle) |

## Key Data Concepts

- **Validator** — runs evals, reports scores, sets on-chain weights
- **Miner** — submits skill packs, gets evaluated per scenario
- **Pack** — a miner's skill submission (identified by SHA-256 hash)
- **Scenario** — an evaluation task (e.g. `client_escalation`, `morning_brief`)
- **Qualification** — pass/fail gate per scenario; miner must pass all to qualify
- **Rejection** — pre-eval failure at `pack_fetch`, `schema_validation`, or `integrity_check` stage
- **Cycle log** — validator's full eval cycle log (metagraph sync → weight submission)
- **Weight** — on-chain weight a validator assigns to a miner; winner gets highest weight
