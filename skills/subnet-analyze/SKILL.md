---
name: subnet-analyze
description: Query and analyze TrajectoryRL subnet (SN11) data — validators, miners, scores, weights, scenarios, eval logs. Use when the user asks about subnet status, validator analysis, miner performance, weight distribution, or wants to run trajrl CLI commands.
---

# Subnet Analyze

Analyze TrajectoryRL subnet data using the `trajrl` CLI.

## Setup

Ensure `trajrl` is installed before running commands:

```bash
pip install trajrl
```

## Commands

Entry point: `trajrl subnet <command>`

### Quick Queries

```bash
trajrl subnet status                    # network overview (validators + submissions)
trajrl subnet submissions               # recent pack submissions
trajrl subnet submissions --failed      # failed submissions only
trajrl subnet download HOTKEY [HASH]    # pack evaluation data
trajrl subnet download --uid <uid>      # download by miner UID
```

### Deep Analysis

The main command — covers validators, scores, weight distribution, scenarios, and miner drill-down in one report.

```bash
trajrl subnet analyze                   # interactive validator picker
trajrl subnet analyze HOTKEY            # analyze a specific validator
trajrl subnet analyze --uid 5           # by validator UID
trajrl subnet analyze HOTKEY --deep     # drill into top miners
trajrl subnet analyze HOTKEY --deep-n 10
trajrl subnet analyze HOTKEY --logs     # include eval logs
trajrl subnet analyze HOTKEY --dump     # dump raw JSON to file
```

The `analyze` command produces:
1. **Score Summary** — miners evaluated, qualification rate, cost/score stats
2. **Rejection Breakdown** — counts by rejection stage
3. **Weight Distribution** — parsed from cycle log, shows per-miner weights, gate status, winner
4. **Scenario Heatmap** — pass rate, avg cost/score per scenario
5. **Top 15 Leaderboard** — miners ranked by score
6. With `--deep`: per-miner drill-down (rank, validators, submissions)

### Global Options

Every `subnet` command accepts:

| Option | Description |
|--------|-------------|
| `--json` / `-j` | Force JSON output (auto when piped) |
| `--base-url` | Override API base URL (env: `TRAJRL_BASE_URL`) |

### JSON Output

When piped, all commands output JSON automatically. Useful for chaining with `jq`:

```bash
trajrl subnet status | jq '.validators.validators[].hotkey'
trajrl subnet submissions | jq '.submissions[] | select(.evalStatus == "failed")'
trajrl subnet download -u 104 | jq '.gcsPackUrl'
```

## Key Data Concepts

- **Validator** — runs evals, reports scores, sets on-chain weights
- **Miner** — submits skill packs, gets evaluated per scenario
- **Pack** — a miner's skill submission (identified by SHA-256 hash)
- **Scenario** — an evaluation task (e.g. `client_escalation`, `morning_brief`)
- **Qualification** — pass/fail gate per scenario; miner must pass all to qualify
- **Rejection** — pre-eval failure at `pack_fetch`, `schema_validation`, or `integrity_check` stage
- **Cycle log** — validator's full eval cycle log (metagraph sync → weight submission)
- **Weight** — on-chain weight a validator assigns to a miner; winner gets highest weight
