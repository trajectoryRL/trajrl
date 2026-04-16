---
name: subnet-analyze
description: Query and analyze TrajectoryRL subnet (SN11) data — validators, miners, scores, weights, scenarios, eval logs. Use when the user asks about subnet status, validator analysis, miner performance, weight distribution, eval debugging, or wants to run trajrl CLI commands.
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
trajrl subnet validators                # all validators with heartbeat + model
trajrl subnet scores --uid 0            # per-miner scores from validator UID 0
trajrl subnet submissions               # recent pack submissions
trajrl subnet submissions --failed      # failed submissions only
trajrl subnet miner --uid 63            # full history for a specific miner
trajrl subnet download --uid 63         # download miner's pack + eval metadata
trajrl subnet download HOTKEY PACK_HASH
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
1. **Score Summary** — miners evaluated, qualification rate, score stats
2. **Rejection Breakdown** — counts by rejection stage
3. **Weight Distribution** — parsed from cycle log, shows per-miner weights, gate status, winner
4. **Scenario Heatmap** — pass rate, avg score per scenario
5. **Top 15 Leaderboard** — miners ranked by score
6. With `--deep`: per-miner drill-down (rank, validators, submissions)

### Eval Logs (debug + audit)

Every evaluation produces a log archive uploaded to GCS. Miner archives include the testee agent's session, the judge agent's grading, per-episode evaluation.json with criteria scores, SKILL.md, JUDGE.md, fixtures, and metadata.

```bash
# List log archives
trajrl subnet logs                               # most recent
trajrl subnet logs --validator HOTKEY --limit 20
trajrl subnet logs --miner HOTKEY
trajrl subnet logs --eval-id 20260329_1430_w42
trajrl subnet logs --pack-hash <sha256>

# Filter by type: 'miner' (per-miner eval) or 'cycle' (validator cycle log)
trajrl subnet logs --type miner --miner HOTKEY
trajrl subnet logs --type cycle --validator HOTKEY

# Show latest matching log
trajrl subnet logs --eval-id <id> --show

# Extract the full archive locally for deep inspection
trajrl subnet logs --eval-id <id> --dump-to ./debug/
```

A Season 1 miner archive has this structure:

```
SKILL.md                                 # miner's pack (the product)
JUDGE.md                                 # scoring rubric used by the judge
metadata.json                            # final_score, mean_quality, delta, episode_qualities
world.json                               # scenario context + validator salt
episodes/episode_N/
  testee_transcript.txt                  # agent's session output
  judge_transcript.txt                   # judge agent's grading session
  evaluation.json                        # per-criterion scores + strengths/weaknesses
  episode.json                           # fixtures + instruction for this episode
```

`--show` on a miner log renders a metadata panel, archive tree, eval summary, and a per-criterion table across all 4 episodes. `--show` on a cycle log prints the validator's `validator.log` text.

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
trajrl subnet logs --eval-id <id> | jq '.logs[0].gcsUrl'
```

## Key Data Concepts

- **Validator** — runs evals, reports scores, sets on-chain weights
- **Miner** — submits a SKILL.md pack, gets evaluated across multiple episodes
- **Pack** — a miner's submission (identified by SHA-256 hash). Season 1 packs contain only `SKILL.md`.
- **Scenario** — an evaluation task (e.g. `incident_response`, `morning_brief`). Each scenario has its own `JUDGE.md` rubric.
- **Episode** — one run of a scenario with fixed fixtures. A full eval is 4 episodes with different fixtures; split-half delta measures learning across them.
- **Final score** — `mean_quality * (1 + 0.5 * max(0, delta))`. Higher wins.
- **Qualification** — pass/fail gate per scenario
- **Rejection** — pre-eval failure at `pack_fetch`, `schema_validation`, or `integrity_check` stage
- **Eval log** — per-miner tar.gz with testee transcript, judge transcript, evaluation.json, SKILL.md, JUDGE.md, fixtures. Retrievable via `trajrl subnet logs`.
- **Cycle log** — validator's full eval cycle log (metagraph sync → weight submission)
- **Weight** — on-chain weight a validator assigns to a miner; winner gets highest weight
