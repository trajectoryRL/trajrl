# trajrl

The official CLI for [TrajectoryRL](https://github.com/trajectoryRL/trajectoryRL) — an open skill factory that leverages Bittensor's distributed compute and incentive layer with reinforcement learning to produce state-of-the-art agent skills.

One install gives any human or AI agent (Claude Code, Cursor, Codex, Hermes, Manus, …) access to every skill TrajectoryRL has shipped. Each skill is a self-contained `SKILL.md` that agents can discover and follow directly.

CLI output is JSON when piped, Rich tables when interactive.

## Install

```bash
pip install trajrl
```

## Subnet queries

```bash
# Network health
trajrl subnet status

# Validator analysis — scores, weights, scenarios, leaderboard
trajrl subnet analyze 5FFApaS7...
trajrl subnet analyze --uid 5 --deep

# Per-miner scores from a specific validator
trajrl subnet scores --uid 0
trajrl subnet scores 5FFApaS7...

# Miner detail — full history and current pack
trajrl subnet miner --uid 63
trajrl subnet miner 5HNEu6jU...

# Download a miner's pack (SKILL.md and evaluation metadata)
trajrl subnet download --uid 63
trajrl subnet download HOTKEY PACK_HASH

# Recent submissions
trajrl subnet submissions
trajrl subnet submissions --failed
```

## Eval logs

Miner and validator logs are uploaded per evaluation and publicly downloadable.

```bash
# List recent eval logs for a validator
trajrl subnet logs --validator HOTKEY --limit 20

# List logs for a specific miner
trajrl subnet logs --miner HOTKEY

# Show the contents of a specific eval (summary + per-criterion scores)
trajrl subnet logs --eval-id 20260329_1430_w42 --show

# Extract the full archive locally for deep inspection
trajrl subnet logs --eval-id 20260329_1430_w42 --dump-to ./debug/
```

A miner eval archive contains:

```
SKILL.md                                 # miner's product
JUDGE.md                                 # scoring rubric used
metadata.json                            # final_score, delta, episode qualities
world.json                               # scenario context + salt
episodes/episode_N/
  testee_transcript.txt                  # agent's Hermes session log
  judge_transcript.txt                   # judge agent's grading log
  evaluation.json                        # per-criterion scores + summary
  episode.json                           # fixtures + instruction
```

Use this to debug SKILL.md iteration, inspect agent behavior, or audit any miner's eval end to end.

## JSON output

Piped output is JSON by default. Use `jq` to compose queries:

```bash
trajrl subnet status | jq '.validators.validators[].hotkey'
trajrl subnet submissions | jq '.submissions[] | select(.evalStatus == "failed")'
trajrl subnet logs --eval-id <id> | jq '.logs[0].gcsUrl'
```

Force JSON in a tty with `--json` / `-j`. Override the API base URL with `--base-url` or `TRAJRL_BASE_URL`.

## Skills

The skill catalog in this repo teaches agents how to use the CLI:

- [`skills/subnet-analyze/SKILL.md`](skills/subnet-analyze/SKILL.md) — query subnet data with `trajrl subnet`

## Links

- **Subnet repo:** https://github.com/trajectoryRL/trajectoryRL — incentive mechanism, evaluation framework, Season 1 spec
- **Bench:** https://github.com/trajectoryRL/trajrl-bench — three-container eval sandbox (sandbox + testee + judge)
- **Website:** https://trajrl.com — leaderboard, live subnet data, dashboards
- **Public API:** [PUBLIC_API.md](https://github.com/trajectoryRL/trajectoryrl.web/blob/main/PUBLIC_API.md) — read-only, no auth, base URL `https://trajrl.com`
