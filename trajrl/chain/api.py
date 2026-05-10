"""Thin wrapper around the bittensor SDK for read-only subnet queries.

Imports of `bittensor` are deferred so that `--help` and `--version` work
without the heavy SDK loaded. Functions return plain dicts to keep the CLI
serialization-friendly.
"""

from __future__ import annotations

from typing import Any


def _subtensor(network: str):
    """Build a `bittensor.subtensor` connection.

    `network` accepts the standard aliases ('finney', 'test', 'local', 'archive')
    or a full `ws(s)://` endpoint URL.
    """
    import bittensor as bt  # deferred to avoid heavy import

    factory = getattr(bt, "Subtensor", None) or getattr(bt, "subtensor", None)
    if factory is None:
        raise RuntimeError("bittensor SDK exposes neither Subtensor nor subtensor")
    return factory(network=network)


def _to_float_list(values: Any) -> list[float]:
    """Convert a tensor / numpy array / list to a plain list[float]."""
    if values is None:
        return []
    try:
        return [float(v) for v in values]
    except TypeError:
        try:
            return [float(v) for v in values.tolist()]
        except Exception:
            return []


def get_metagraph(netuid: int, network: str = "finney") -> dict[str, Any]:
    """Fetch the metagraph for `netuid` and return a serializable dict."""
    subtensor = _subtensor(network)
    mg = subtensor.metagraph(netuid=netuid)

    uids = list(getattr(mg, "uids", []) or [])
    hotkeys = list(getattr(mg, "hotkeys", []) or [])
    coldkeys = list(getattr(mg, "coldkeys", []) or [])
    stake = _to_float_list(getattr(mg, "stake", None) or getattr(mg, "total_stake", None))
    incentive = _to_float_list(getattr(mg, "incentive", None))
    dividends = _to_float_list(getattr(mg, "dividends", None))
    trust = _to_float_list(getattr(mg, "trust", None))
    consensus = _to_float_list(getattr(mg, "consensus", None))
    emission = _to_float_list(getattr(mg, "emission", None))
    active = list(getattr(mg, "active", []) or [])
    validator_permit = list(getattr(mg, "validator_permit", []) or [])
    last_update = list(getattr(mg, "last_update", []) or [])

    n = len(uids)

    def _at(seq, i, default=None):
        try:
            return seq[i]
        except (IndexError, TypeError):
            return default

    neurons = []
    for i in range(n):
        neurons.append(
            {
                "uid": int(_at(uids, i, i)),
                "hotkey": str(_at(hotkeys, i, "")),
                "coldkey": str(_at(coldkeys, i, "")),
                "stake": float(_at(stake, i, 0.0) or 0.0),
                "incentive": float(_at(incentive, i, 0.0) or 0.0),
                "dividends": float(_at(dividends, i, 0.0) or 0.0),
                "trust": float(_at(trust, i, 0.0) or 0.0),
                "consensus": float(_at(consensus, i, 0.0) or 0.0),
                "emission": float(_at(emission, i, 0.0) or 0.0),
                "active": bool(_at(active, i, False)),
                "validator_permit": bool(_at(validator_permit, i, False)),
                "last_update": int(_at(last_update, i, 0) or 0),
            }
        )

    return {
        "netuid": netuid,
        "network": network,
        "block": int(getattr(mg, "block", 0) or 0) or None,
        "n": n,
        "neurons": neurons,
    }


def get_emission(netuid: int, network: str = "finney") -> dict[str, Any]:
    """Fetch subnet-level emission and core hyperparams."""
    subtensor = _subtensor(network)
    out: dict[str, Any] = {"netuid": netuid, "network": network}

    info = None
    for getter_name in ("get_subnet_info", "subnet_info"):
        getter = getattr(subtensor, getter_name, None)
        if callable(getter):
            try:
                info = getter(netuid=netuid)
                break
            except Exception:
                continue

    if info is not None:
        out["emission"] = _maybe_float(getattr(info, "emission_value", None))
        out["max_neurons"] = _maybe_int(getattr(info, "max_n", None))

    hp = None
    for getter_name in (
        "get_subnet_hyperparameters",
        "subnet_hyperparameters",
    ):
        getter = getattr(subtensor, getter_name, None)
        if callable(getter):
            try:
                hp = getter(netuid=netuid)
                break
            except Exception:
                continue

    if hp is not None:
        out["tempo"] = _maybe_int(getattr(hp, "tempo", None))
        burn = _maybe_float(getattr(hp, "burn", None) or getattr(hp, "registration_cost", None))
        if burn is not None:
            out["burn"] = burn
            out["registration_cost"] = burn
        out["max_neurons"] = out.get("max_neurons") or _maybe_int(getattr(hp, "max_n", None))
        out["min_allowed_weights"] = _maybe_int(getattr(hp, "min_allowed_weights", None))
        out["max_weights_limit"] = _maybe_int(getattr(hp, "max_weights_limit", None))
        out["weights_rate_limit"] = _maybe_int(getattr(hp, "weights_rate_limit", None))
        out["immunity_period"] = _maybe_int(getattr(hp, "immunity_period", None))
        out["activity_cutoff"] = _maybe_int(getattr(hp, "activity_cutoff", None))

    return out


def _maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(value.tao)  # type: ignore[union-attr]
        except Exception:
            return None
