# trajrl

The official Python CLI for [TrajectoryRL](https://github.com/trajectoryRL/trajectoryRL) — an open skill factory that uses Bittensor's distributed compute and incentive layer to produce state-of-the-art agent skills.

One install, one binary, two groups:

| Group | What it does |
|---|---|
| `trajrl skills ...` | Browse and install agent skills published on `trajrl.com` into your local agent skill dirs (Claude Code, Cursor, Codex, Hermes, OpenClaw). |
| `trajrl <subnet command>` | Live SN11 state — winner, challenger, queue, validators, miners, packs, eval logs, deep validator analysis. |

CLI output is Rich tables in a TTY and JSON when piped.

For generic Bittensor on-chain queries (metagraph, hyperparams) use [`btcli`](https://github.com/opentensor/btcli) — the official Bittensor CLI.

## Install

```bash
pip install trajrl
```

## Live SN11 state (v6 winner-challenger)

```bash
trajrl challenge                    # in-flight epoch — challenger pack + per-validator scores so far
trajrl winner                       # current seated winner + last 5 change events
trajrl winner --history 20          # show more history
trajrl queue                        # pending eval queue
trajrl queue --eligible-only        # filter to submissions eligible right now
```

## Validators / miners / packs

```bash
trajrl validators                   # roster table
trajrl validators --detail          # adds stake / weightTargets / benchVersion
trajrl miner --uid 63               # miner detail by UID
trajrl miner HOTKEY
trajrl pack HOTKEY PACK_HASH        # specific pack + eval results
trajrl submissions                  # recent submissions across the network
trajrl submissions --failed
```

## Subnet analysis

```bash
trajrl analyze                              # last 24h, all reports
trajrl analyze --epochs 50                  # explicit epoch window
trajrl analyze --last 6                     # last 6 hours
trajrl analyze --scenario cancel-async-tasks   # focus per-scenario report
trajrl analyze --no-compare                 # skip the validator-sync table
trajrl analyze --deep                       # drill into eval logs for top packs
```

`analyze` produces, in one report:

1. **Throughput** — epochs in window, decisions submitted, decisions/hour, rejection rate
2. **Competition Health** — distinct challenger packs/miners, outcomes (held/replaced), replace rate, current winner tenure, mean inter-replacement gap
3. **Score Distribution** — N qualified, mean, p50/p75/p90/p99, histogram of consensus_score
4. **Per-Scenario** — pass rate, mean score, eval count, top-scoring pack per scenario (filterable with `--scenario`)
5. **Top 10 Challenger Packs** — best consensus_score in window, with outcome
6. **Rejection Breakdown** — bucketed reasons (integrity:copy, eval_error, schema_validation, etc.) with sample details
7. **Miner Pool** — distinct miners, distinct packs, top-10 most-active
8. **Validator Sync** — per-validator mean Δ vs peer mean; outlier flag with adaptive threshold (1.5× network median)
9. **Recent Winner Changes** — last 10 replacement events
10. With `--deep`: drill into eval logs for the top challenger packs in the window

## Eval logs (debug + audit)

```bash
trajrl logs --validator HOTKEY --limit 20
trajrl logs --eval-id 20260329_1430_w42 --show
trajrl logs --eval-id 20260329_1430_w42 --dump-to ./debug/
```

A miner eval archive contains:

```
SKILL.md                                 # miner's product
JUDGE.md                                 # scoring rubric used
metadata.json                            # final_score, delta, episode qualities
world.json                               # scenario context + salt
episodes/episode_N/
  testee_transcript.txt                  # agent's session log
  judge_transcript.txt                   # judge agent's grading log
  evaluation.json                        # per-criterion scores + summary
  episode.json                           # fixtures + instruction
```

## Skill hub

```bash
trajrl skills list                              # all available skills
trajrl skills list --tag dev-tools --tag data   # filter by tags (AND)
trajrl skills search "code review"
trajrl skills show self-learning
trajrl skills add self-learning                 # install into every detected agent
trajrl skills add self-learning --agent cursor
trajrl skills sync                              # re-pull installed skills if newer upstream
```

Default agent skill directories (auto-detected by directory existence):

| Agent | Path |
|---|---|
| Claude Code | `~/.claude/skills/<slug>/SKILL.md` |
| Cursor | `~/.cursor/skills-cursor/<slug>/SKILL.md` |
| Codex | `~/.codex/skills/<slug>/SKILL.md` |
| Hermes | `~/.hermes/skills/<slug>/SKILL.md` |
| OpenClaw | `~/.openclaw/skills/<slug>/SKILL.md` |

## Global options

Every command accepts:

| Option | Description |
|---|---|
| `--json` / `-j` | Force JSON output (auto when piped) |
| `--base-url` | Override API base URL (env: `TRAJRL_BASE_URL`) |
| `--version` / `-v` | Print version and exit |

## JSON output

Piped output is JSON for every command — handy with `jq`:

```bash
trajrl skills list | jq '.skills[].slug'
trajrl winner | jq '.current.winner.uid'
trajrl queue --eligible-only | jq '.queue | length'
trajrl validators | jq '.validators[] | {uid, name, version, weightTargets}'
```

## Skills (in this repo)

- [`skills/trajrl/SKILL.md`](skills/trajrl/SKILL.md) — full agent-facing reference

## Migration from v1.x

v1.x shipped three binaries: `trajrl`, `trajectoryrl-inspector`, `bittensor-subnet-inspector`. v2.0 collapses everything into one `trajrl` binary.

| v1.x | v2.0 |
|---|---|
| `trajectoryrl-inspector status` | `trajrl validators` |
| `trajectoryrl-inspector download HOTKEY HASH` | `trajrl pack HOTKEY HASH` |
| `trajectoryrl-inspector download --uid N` | `trajrl miner --uid N` |
| `trajectoryrl-inspector analyze HOTKEY` | `trajrl analyze HOTKEY` |
| `trajectoryrl-inspector logs ...` | `trajrl logs ...` |
| `trajectoryrl-inspector submissions` | `trajrl submissions` |
| `bittensor-subnet-inspector metagraph -u 11` | `btcli subnet metagraph --netuid 11` (no longer in trajrl) |
| `bittensor-subnet-inspector emission -u 11` | `btcli subnet hyperparameters --netuid 11` (no longer in trajrl) |

New v2.0 commands: `trajrl challenge`, `trajrl winner`, `trajrl queue` (v6 dual-seat winner-challenger).

**v2.1 (this release):** removed `trajrl chain` group — it was redundant with `btcli` and pulled in the heavy `bittensor` SDK as a hard dependency. v2.1 has no chain-query commands; use `btcli subnet metagraph` / `btcli subnet hyperparameters` instead. Result: much lighter install (no substrate-interface, scalecodec, websockets, etc.).

## Links

- **Subnet repo:** https://github.com/trajectoryRL/trajectoryRL — incentive mechanism, evaluation framework
- **Bench:** https://github.com/trajectoryRL/trajrl-bench — eval sandbox
- **Website:** https://trajrl.com — leaderboard, live subnet data, skill hub
- **Public API:** [PUBLIC_API.md](https://github.com/trajectoryRL/trajectoryrl.web/blob/main/PUBLIC_API.md) — read-only, no auth, base URL `https://trajrl.com`
