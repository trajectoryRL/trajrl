---
name: trajrl
description: Official Python CLI for TrajectoryRL (Bittensor SN11). One binary, three groups — skill hub install, live SN11 state (challenge/winner/queue + validator/miner/pack/analyze/logs), and generic Bittensor on-chain queries. Use when the user asks about SN11 internals, eval debugging, validator analysis, or chain state for any Bittensor subnet.
---

# trajrl

Official Python CLI for [TrajectoryRL](https://github.com/trajectoryRL/trajectoryRL) (Bittensor SN11). Reads the public API at `https://trajrl.com` plus the Bittensor chain.

## Setup

```bash
pip install trajrl
```

One binary: `trajrl`. Output is Rich tables in a TTY and JSON when piped.

## Command surface

```
trajrl
├── skills              skill hub (browse + install agent skills)
├── challenge           in-flight epoch — challenger pack + per-validator scores
├── winner [--history N]  current seated winner; --history shows change events (default 5)
├── queue [--limit N --eligible-only]  pending eval queue
├── validators [--detail]   validator roster
├── miner HOTKEY|--uid N    miner detail (current pack, score, validator reports)
├── pack HOTKEY HASH        download a specific pack + eval results
├── submissions [--failed]  recent miner submissions
├── analyze VALIDATOR       validator deep-dive
├── logs                    eval-log archives (list / --show / --dump-to)
└── chain                   generic Bittensor on-chain queries
    ├── metagraph
    └── emission
```

## Live state (v6 winner-challenger)

The subnet runs a dual-seated mechanism: at any time there is one **seated winner** + one **challenger** under evaluation each epoch.

```bash
trajrl challenge                    # who's in flight, what each validator has scored
trajrl winner                       # current seated winner + last 5 change events
trajrl winner --history 20          # extend history depth
trajrl winner --history 0           # current only
trajrl queue                        # what's waiting to be picked up
trajrl queue --eligible-only        # filter to submissions eligible right now
```

## Validators / miners / packs

```bash
trajrl validators                   # roster table
trajrl validators --detail          # adds stake / weightTargets / benchVersion
trajrl miner HOTKEY                 # full miner detail
trajrl miner --uid 63
trajrl pack HOTKEY PACK_HASH        # specific pack + eval results
trajrl submissions                  # recent submissions across the network
trajrl submissions --failed
```

## Validator deep-dive

The main analytical command. One report covers scores, weight distribution (parsed from cycle log), scenario heatmap, and a top-15 leaderboard.

```bash
trajrl analyze                      # interactive validator picker
trajrl analyze HOTKEY               # specific validator
trajrl analyze --uid 5
trajrl analyze HOTKEY --deep        # drill into top miners
trajrl analyze HOTKEY --deep-n 10
trajrl analyze HOTKEY --logs        # include recent eval logs
trajrl analyze HOTKEY --dump        # raw JSON to file
```

## Eval logs (debug + audit)

Every evaluation produces a tar.gz archive uploaded to GCS. Miner archives include the testee agent's session, the judge agent's grading, per-episode `evaluation.json`, plus `SKILL.md`, `JUDGE.md`, fixtures and metadata.

```bash
trajrl logs                                 # most recent
trajrl logs --validator HOTKEY --limit 20
trajrl logs --miner HOTKEY
trajrl logs --eval-id 20260329_1430_w42
trajrl logs --pack-hash <sha256>
trajrl logs --type miner --miner HOTKEY     # filter by archive type
trajrl logs --type cycle --validator HOTKEY
trajrl logs --eval-id <id> --show           # download + render
trajrl logs --eval-id <id> --dump-to ./debug/   # extract for local inspection
```

A Season 1 miner archive layout:

```
SKILL.md                                 # miner's pack (the product)
JUDGE.md                                 # scoring rubric used by the judge
metadata.json                            # final_score, mean_quality, delta, episode_qualities
world.json                               # scenario context + validator salt
episodes/episode_N/
  testee_transcript.txt                  # agent's session output
  judge_transcript.txt                   # judge's grading session
  evaluation.json                        # per-criterion scores
  episode.json                           # fixtures + instruction
```

## Chain queries (any subnet)

```bash
trajrl chain metagraph --netuid 11
trajrl chain metagraph --netuid 11 --network test
trajrl chain emission --netuid 11
```

`--network` accepts `finney` (default) | `test` | `local` | `archive` | `ws(s)://endpoint`. Env: `BT_NETWORK`.

## Skill hub

```bash
trajrl skills list                              # all available skills
trajrl skills list --tag dev-tools --tag data   # filter (AND on tags)
trajrl skills search "code review"
trajrl skills show self-learning
trajrl skills add self-learning                 # install into every detected agent
trajrl skills add self-learning --agent cursor
trajrl skills sync
```

## Global options

Every command accepts:

| Option | Description |
|---|---|
| `--json` / `-j` | Force JSON output (auto when piped) |
| `--base-url` | Override API base URL (env: `TRAJRL_BASE_URL`) |
| `--version` / `-v` | Print version and exit |

`trajrl chain` commands additionally accept `--network` / `-n`.

## JSON output

Piped output is JSON for every command:

```bash
trajrl winner | jq '.current.winner.uid'
trajrl queue --eligible-only | jq '.queue | length'
trajrl validators | jq '.validators[] | {uid, name, version, weightTargets}'
trajrl chain metagraph -u 11 | jq '.neurons | sort_by(-.incentive) | .[0:5]'
trajrl logs --eval-id <id> | jq '.logs[0].gcsUrl'
```

## Key data concepts

**Subnet (v6 dual-seat)**

- **Seated winner** — the pack currently earning emission. Persists until a challenger beats it (with margin).
- **Challenger** — the pack under evaluation this epoch. One per epoch.
- **Epoch** — fixed-length block window during which validators evaluate the challenger and submit scores.
- **Quorum** — fraction of stake-weighted validators needed for an epoch to finalize.
- **Outcome** — `winner_held` (challenger lost) or `winner_replaced` (challenger took the seat).
- **Cooldown** — minimum hours between submissions from the same miner.

**Evaluation**

- **Pack** — a miner's submission (SHA-256 hash). Currently `SKILL.md` only.
- **Scenario** — an evaluation task. Each has its own judge rubric.
- **Episode** — one run of a scenario with fixed fixtures.
- **Final score** — `mean_quality * (1 + 0.5 * max(0, delta))`. Higher wins.
- **Qualified / Rejected** — qualification gate per scenario; rejection happens at `pack_fetch`, `schema_validation`, or `integrity_check`.
- **Eval log** — per-miner tar.gz with transcripts + evaluation.json + fixtures.
- **Cycle log** — validator's full eval-cycle log (metagraph sync → weight submission).

**Chain**

- **netuid** — subnet identifier. SN11 = TrajectoryRL.
- **metagraph** — per-block snapshot of all neurons on a subnet.
- **stake** — TAO bonded to a neuron's hotkey (including delegations).
- **incentive** — miner's emission share, derived from validator scores.
- **dividends** — validator's emission share, from miners they scored.
- **trust / consensus** — validator-agreement metrics.
- **tempo** — block interval between weight settlements.
- **burn / registration_cost** — TAO cost to register a hotkey.
