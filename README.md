# trajrl

The official Python toolbelt for [TrajectoryRL](https://github.com/trajectoryRL/trajectoryRL) — an open skill factory that uses Bittensor's distributed compute and incentive layer with reinforcement learning to produce state-of-the-art agent skills.

A single `pip install trajrl` ships **three CLI binaries**:

| Binary | Purpose |
|--------|---------|
| `trajrl` | **Skill hub installer.** Browse and install agent skills published on `trajrl.com` into your local agent skill directories (Claude Code, Cursor, Codex, Hermes, OpenClaw). Mirrors the npm `trajrl` CLI. |
| `trajectoryrl-inspector` | **TrajectoryRL / SN11 deep analysis.** Validators, miners, scores, weight distribution, scenario heatmaps, eval log archives. |
| `bittensor-subnet-inspector` | **Generic Bittensor on-chain queries** for any subnet — metagraph and subnet hyperparams (tempo / emission / burn). |

CLI output is Rich tables in a TTY and JSON when piped.

## Install

```bash
pip install trajrl
```

The PyPI distribution name is intentionally still `trajrl` while the layout stabilizes; see the roadmap in [`CLAUDE.md`](CLAUDE.md).

## `trajrl` — skill hub installer

```bash
trajrl skills list                              # all available skills
trajrl skills list --tag dev-tools --tag data   # filter by tags (AND)
trajrl skills search "code review"              # free-text search
trajrl skills show self-learning                # render full SKILL.md
trajrl skills add self-learning                 # install into every detected agent
trajrl skills add self-learning --agent cursor  # only install for Cursor
trajrl skills add self-learning --target ./local-skills
trajrl skills sync                              # re-pull installed skills if newer upstream
trajrl skills sync --dry-run
```

Default agent skill directories (auto-detected by directory existence):

| Agent | Path |
|-------|------|
| Claude Code | `~/.claude/skills/<slug>/SKILL.md` |
| Cursor | `~/.cursor/skills-cursor/<slug>/SKILL.md` |
| Codex | `~/.codex/skills/<slug>/SKILL.md` |
| Hermes | `~/.hermes/skills/<slug>/SKILL.md` |
| OpenClaw | `~/.openclaw/skills/<slug>/SKILL.md` |

## `trajectoryrl-inspector` — SN11 analysis

```bash
trajectoryrl-inspector status                   # network health
trajectoryrl-inspector analyze --uid 5 --deep   # full validator analysis with miner drill-down
trajectoryrl-inspector analyze HOTKEY --logs    # include recent eval logs

trajectoryrl-inspector submissions              # recent pack submissions
trajectoryrl-inspector submissions --failed
trajectoryrl-inspector download --uid 63        # download a miner's pack + metadata
trajectoryrl-inspector download HOTKEY PACK_HASH

trajectoryrl-inspector logs --validator HOTKEY --limit 20
trajectoryrl-inspector logs --eval-id 20260329_1430_w42 --show
trajectoryrl-inspector logs --eval-id 20260329_1430_w42 --dump-to ./debug/
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

Override the API base URL with `--base-url` or `TRAJRL_BASE_URL`.

## `bittensor-subnet-inspector` — generic chain queries

```bash
bittensor-subnet-inspector metagraph --netuid 11
bittensor-subnet-inspector metagraph --netuid 11 --network test
bittensor-subnet-inspector emission --netuid 11
```

Override the network with `--network` or `BT_NETWORK` (`finney` | `test` | `local` | `archive` | `ws(s)://endpoint`).

## JSON output

Piped output is JSON by default for every binary. Force JSON in a TTY with `--json` / `-j`.

```bash
trajrl skills list --json | jq '.skills[].slug'
trajectoryrl-inspector status | jq '.validators.validators[].hotkey'
bittensor-subnet-inspector metagraph -u 11 | jq '.neurons[0:5]'
```

## Skills

The skill catalog in this repo teaches agents how to use the binaries:

- [`skills/trajectoryrl-inspector/SKILL.md`](skills/trajectoryrl-inspector/SKILL.md)
- [`skills/bittensor-subnet-inspector/SKILL.md`](skills/bittensor-subnet-inspector/SKILL.md)

## Links

- **Subnet repo:** https://github.com/trajectoryRL/trajectoryRL — incentive mechanism, evaluation framework, Season 1 spec
- **Bench:** https://github.com/trajectoryRL/trajrl-bench — three-container eval sandbox (sandbox + testee + judge)
- **Website:** https://trajrl.com — leaderboard, live subnet data, dashboards, skill hub
- **Public API:** [PUBLIC_API.md](https://github.com/trajectoryRL/trajectoryrl.web/blob/main/PUBLIC_API.md) — read-only, no auth, base URL `https://trajrl.com`
