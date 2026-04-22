---
name: bittensor-subnet-inspector
description: Generic on-chain queries for any Bittensor subnet — metagraph (per-neuron stake/incentive/dividends/trust/consensus) and subnet hyperparams (tempo, emission, registration burn). Use when the user asks about Bittensor chain state on any subnet, not just TrajectoryRL/SN11.
---

# Bittensor Subnet Inspector

Read-only on-chain query tool for any Bittensor subnet. Wraps the `bittensor` SDK so the agent does not need to write Python to inspect chain state.

## Setup

Install the toolbelt (provides this binary plus `trajectoryrl-inspector` and `trajrl`):

```bash
pip install trajrl
```

The PyPI distribution name is intentionally still `trajrl` while the layout stabilizes; the binary you run is `bittensor-subnet-inspector`.

## Commands

Entry point: `bittensor-subnet-inspector <command>`.

### Metagraph

```bash
bittensor-subnet-inspector metagraph --netuid 11
bittensor-subnet-inspector metagraph --netuid 11 --network test
bittensor-subnet-inspector metagraph --netuid 11 --json | jq '.neurons[0]'
```

Returns one row per neuron with: `uid`, `hotkey`, `coldkey`, `stake`, `incentive`, `dividends`, `trust`, `consensus`, `emission`, `active`, `validator_permit`, `last_update`.

### Emission and hyperparams

```bash
bittensor-subnet-inspector emission --netuid 11
bittensor-subnet-inspector emission --netuid 11 --json
```

Returns subnet-level: `tempo`, `emission`, `burn` (registration cost in TAO), `registration_cost` (alias of burn), `max_neurons`, `min_allowed_weights`, `max_weights_limit`, `weights_rate_limit`, `immunity_period`, `activity_cutoff`.

### Global options

| Option | Description |
|--------|-------------|
| `--netuid` / `-u` | Subnet UID (required) |
| `--network` / `-n` | `finney` (default) \| `test` \| `local` \| `archive` \| `ws(s)://endpoint`. Env: `BT_NETWORK`. |
| `--json` / `-j` | Force JSON output (auto when piped) |

### JSON output

When piped, output is JSON. Useful for chaining:

```bash
bittensor-subnet-inspector metagraph --netuid 11 | \
  jq '.neurons | sort_by(.incentive) | reverse | .[0:5]'

bittensor-subnet-inspector emission --netuid 11 | jq '.tempo, .burn'
```

## Key data concepts

- **netuid** — subnet identifier on Bittensor. SN11 = TrajectoryRL.
- **metagraph** — per-block snapshot of all neurons (validators + miners) on a subnet.
- **stake** — TAO bonded to a neuron's hotkey, including delegations.
- **incentive** — share of subnet emission a miner earns based on validator scores.
- **dividends** — share of subnet emission a validator earns from miners they scored.
- **trust** — average normalized weight a neuron receives across validators.
- **consensus** — agreement metric: how closely a neuron's weights match the median.
- **emission** — TAO emitted to a neuron per block.
- **validator_permit** — whether a neuron is allowed to set weights this epoch.
- **tempo** — block interval between weight settlements for the subnet.
- **burn / registration_cost** — TAO cost to register a new hotkey.

## Companion skill

For TrajectoryRL/SN11-specific deep analysis (miner submissions, eval log archives, per-scenario scoring) use the `trajectoryrl-inspector` skill.
