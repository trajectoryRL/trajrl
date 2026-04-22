---
name: trajectoryrl-inspector
description: Deep analysis CLI for the TrajectoryRL subnet (Bittensor SN11) — miner submissions, validator scores, weight distribution, scenario heatmaps, eval log archives. Use when the user asks about SN11 internals: validator analysis, miner performance, eval debugging, or wants to drive the trajectoryrl-inspector CLI.
---

# TrajectoryRL Inspector

Deep analysis tool for TrajectoryRL (Bittensor SN11). Talks to the read-only public API at `https://trajrl.com`.

## Setup

Install the toolbelt (provides this binary plus `bittensor-subnet-inspector` and `trajrl`):

```bash
pip install trajrl
```

The PyPI distribution name is intentionally still `trajrl` while the layout stabilizes; the binary you run is `trajectoryrl-inspector`.

## Commands

Entry point: `trajectoryrl-inspector <command>` (formerly `trajrl subnet <command>` — the old binary is gone).

### Quick queries

```bash
trajectoryrl-inspector status                        # validators + recent submissions overview
trajectoryrl-inspector submissions                   # recent pack submissions
trajectoryrl-inspector submissions --failed          # failed submissions only
trajectoryrl-inspector download --uid 63             # download a miner's pack + eval metadata
trajectoryrl-inspector download HOTKEY PACK_HASH
```

### Deep analysis

The main command — covers validators, scores, weight distribution, scenarios and a leaderboard in one report.

```bash
trajectoryrl-inspector analyze                       # interactive validator picker
trajectoryrl-inspector analyze HOTKEY                # analyze a specific validator
trajectoryrl-inspector analyze --uid 5               # by validator UID
trajectoryrl-inspector analyze HOTKEY --deep         # drill into top miners
trajectoryrl-inspector analyze HOTKEY --deep-n 10
trajectoryrl-inspector analyze HOTKEY --logs         # include recent eval logs
trajectoryrl-inspector analyze HOTKEY --dump         # dump raw JSON to file
```

`analyze` produces:
1. **Score Summary** — miners evaluated, qualification rate, score stats
2. **Rejection Breakdown** — counts by rejection stage
3. **Weight Distribution** — parsed from cycle log, per-miner weights, gate status, winner
4. **Scenario Heatmap** — pass rate, avg score per scenario
5. **Top 15 Leaderboard** — miners ranked by score
6. With `--deep`: per-miner drill-down (rank, validators, submissions)

### Eval logs (debug + audit)

Every evaluation produces a log archive uploaded to GCS. Miner archives include the testee agent's session, the judge agent's grading, per-episode `evaluation.json` with criteria scores, `SKILL.md`, `JUDGE.md`, fixtures and metadata.

```bash
trajectoryrl-inspector logs                                  # most recent
trajectoryrl-inspector logs --validator HOTKEY --limit 20
trajectoryrl-inspector logs --miner HOTKEY
trajectoryrl-inspector logs --eval-id 20260329_1430_w42
trajectoryrl-inspector logs --pack-hash <sha256>

# Filter by type: 'miner' (per-miner eval) or 'cycle' (validator cycle log)
trajectoryrl-inspector logs --type miner --miner HOTKEY
trajectoryrl-inspector logs --type cycle --validator HOTKEY

# Show the latest matching log
trajectoryrl-inspector logs --eval-id <id> --show

# Extract the full archive locally for deep inspection
trajectoryrl-inspector logs --eval-id <id> --dump-to ./debug/
```

A Season 1 miner archive layout:

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

`--show` on a miner log renders metadata, archive tree, eval summary and a per-criterion table across all 4 episodes. `--show` on a cycle log prints the validator's `validator.log`.

### Global options

Every command accepts:

| Option | Description |
|--------|-------------|
| `--json` / `-j` | Force JSON output (auto when piped) |
| `--base-url` | Override API base URL (env: `TRAJRL_BASE_URL`) |

### JSON output

When piped, all commands output JSON automatically — useful for `jq`:

```bash
trajectoryrl-inspector status | jq '.validators.validators[].hotkey'
trajectoryrl-inspector submissions | jq '.submissions[] | select(.evalStatus == "failed")'
trajectoryrl-inspector download -u 104 | jq '.gcsPackUrl'
trajectoryrl-inspector logs --eval-id <id> | jq '.logs[0].gcsUrl'
```

## Key data concepts

- **Validator** — runs evals, reports scores, sets on-chain weights
- **Miner** — submits a `SKILL.md` pack, gets evaluated across multiple episodes
- **Pack** — a miner's submission (identified by SHA-256 hash). Season 1 packs contain only `SKILL.md`.
- **Scenario** — an evaluation task (e.g. `incident_response`, `morning_brief`). Each scenario has its own `JUDGE.md` rubric.
- **Episode** — one run of a scenario with fixed fixtures. A full eval is 4 episodes with different fixtures; split-half delta measures learning across them.
- **Final score** — `mean_quality * (1 + 0.5 * max(0, delta))`. Higher wins.
- **Qualification** — pass/fail gate per scenario
- **Rejection** — pre-eval failure at `pack_fetch`, `schema_validation` or `integrity_check` stage
- **Eval log** — per-miner tar.gz with testee transcript, judge transcript, evaluation.json, SKILL.md, JUDGE.md, fixtures
- **Cycle log** — validator's full eval cycle log (metagraph sync → weight submission)
- **Weight** — on-chain weight a validator assigns to a miner; the winner gets the highest weight

## Companion skill

For generic Bittensor on-chain queries (any subnet, not SN11-specific) use the `bittensor-subnet-inspector` skill.
