"""Typed HTTP client for the TrajectoryRL public API."""

from __future__ import annotations

import gzip
import io
import tarfile
from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://trajrl.com"
_TIMEOUT = 30.0


def extract_cycle_log(archive_bytes: bytes) -> str | None:
    """Extract validator.log text from a cycle log archive (tar.gz or gzip)."""
    try:
        buf = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("validator.log"):
                    f = tar.extractfile(member)
                    if f:
                        return f.read().decode("utf-8", errors="replace")
    except Exception:
        pass
    try:
        return gzip.decompress(archive_bytes).decode("utf-8", errors="replace")
    except Exception:
        pass
    return archive_bytes.decode("utf-8", errors="replace")


def list_archive_members(archive_bytes: bytes) -> list[tuple[str, int]]:
    """Return a list of (name, size) tuples for all files in a tar.gz archive."""
    try:
        buf = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            return sorted(
                (m.name, m.size)
                for m in tar.getmembers() if m.isfile()
            )
    except Exception:
        return []


def extract_archive_file(archive_bytes: bytes, name: str) -> str | None:
    """Read one file from a tar.gz archive as text. Returns None if missing."""
    try:
        buf = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name == name or member.name.endswith("/" + name):
                    f = tar.extractfile(member)
                    if f:
                        return f.read().decode("utf-8", errors="replace")
    except Exception:
        pass
    return None


def extract_archive_to_dir(archive_bytes: bytes, out_dir: "str") -> None:
    """Extract a tar.gz archive to a directory."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    buf = io.BytesIO(archive_bytes)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        tar.extractall(out_dir)


@dataclass
class TrajRLClient:
    base_url: str = DEFAULT_BASE_URL
    _client: httpx.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=_TIMEOUT,
            headers={"Accept": "application/json"},
        )

    # -- endpoints ---------------------------------------------------------

    def validators(self) -> dict[str, Any]:
        """GET /api/validators"""
        return self._get("/api/validators")

    def scores_by_validator(self, validator: str | None = None, uid: int | None = None) -> dict[str, Any]:
        """GET /api/scores/by-validator?validator=<hotkey> or resolve UID to hotkey."""
        if uid is not None:
            validators_data = self.validators()
            for vali in validators_data.get("validators", []):
                if vali.get("uid") == uid:
                    validator = vali.get("hotkey")
                    if validator:
                        return self._get("/api/scores/by-validator", params={"validator": validator})
            raise ValueError(f"Could not find validator with UID {uid}")
        if validator is None:
            raise ValueError("Either validator hotkey or uid must be provided")
        return self._get("/api/scores/by-validator", params={"validator": validator})

    def miner(self, hotkey: str | None = None, uid: int | None = None) -> dict[str, Any]:
        """GET /api/miners/:hotkey or resolve UID to hotkey first."""
        if uid is not None:
            validators_data = self.validators()
            for vali in validators_data.get("validators", []):
                vali_key = vali.get("hotkey")
                if vali_key:
                    try:
                        scores = self.scores_by_validator(vali_key)
                        for entry in scores.get("entries", []):
                            if entry.get("uid") == uid:
                                hotkey = entry.get("minerHotkey")
                                if hotkey:
                                    return self._get(f"/api/miners/{hotkey}")
                    except Exception:
                        continue
            raise ValueError(f"Could not resolve UID {uid} to a miner hotkey")
        if hotkey is None:
            raise ValueError("Either hotkey or uid must be provided")
        return self._get(f"/api/miners/{hotkey}")

    def pack(self, hotkey: str, pack_hash: str) -> dict[str, Any]:
        """GET /api/miners/:hotkey/packs/:packHash"""
        return self._get(f"/api/miners/{hotkey}/packs/{pack_hash}")

    def submissions(self, limit: int | None = None) -> dict[str, Any]:
        """GET /api/submissions"""
        return self._get("/api/submissions", params=_compact({"limit": limit}))

    def eval_logs(
        self,
        *,
        validator: str | None = None,
        miner: str | None = None,
        log_type: str | None = None,
        eval_id: str | None = None,
        pack_hash: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """GET /api/eval-logs"""
        params = _compact({
            "validator": validator,
            "miner": miner,
            "type": log_type,
            "eval_id": eval_id,
            "pack_hash": pack_hash,
            "from": from_date,
            "to": to_date,
            "limit": limit,
            "offset": offset,
        })
        return self._get("/api/eval-logs", params=params)

    def log_archive(
        self,
        *,
        validator: str | None = None,
        miner: str | None = None,
        log_type: str | None = None,
        eval_id: str | None = None,
        pack_hash: str | None = None,
    ) -> dict[str, Any]:
        """Fetch the latest matching log archive, return metadata + raw bytes.

        Generic retrieval path used by `trajrl logs --show`. Returns
        ``{"log_entry": <metadata dict>, "archive": <raw tar.gz bytes>}``.

        ``log_type`` is optional — omit to match any (miner or cycle).
        At least one filter should be provided; otherwise this returns the
        most recent archive for anyone on the network.

        Raises ``ValueError`` when no archive matches or download fails.
        """
        params: dict[str, Any] = {"limit": 5}
        if validator is not None:
            params["validator"] = validator
        if miner is not None:
            params["miner"] = miner
        if log_type is not None:
            params["log_type"] = log_type
        if eval_id is not None:
            params["eval_id"] = eval_id
        if pack_hash is not None:
            params["pack_hash"] = pack_hash

        data = self.eval_logs(**params)
        logs = data.get("logs", [])
        if not logs:
            raise ValueError("No matching log archives found")

        log_entry = logs[0]
        gcs_url = log_entry.get("gcsUrl")
        if not gcs_url:
            raise ValueError("Log archive has no download URL")

        try:
            resp = httpx.get(gcs_url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:
            raise ValueError(f"Failed to download log archive: {exc}") from exc

        return {"log_entry": log_entry, "archive": resp.content}

    def cycle_log(
        self,
        validator: str,
        *,
        eval_id: str | None = None,
    ) -> dict[str, Any]:
        """Backwards-compat: fetch the latest cycle log text for a validator.

        Returns ``{"log_entry": ..., "text": <validator.log text>}``.
        Prefer ``log_archive()`` for new code.
        """
        result = self.log_archive(
            validator=validator,
            log_type="cycle",
            eval_id=eval_id,
        )
        text = extract_cycle_log(result["archive"])
        if not text:
            raise ValueError("Failed to extract validator.log from archive")
        return {"log_entry": result["log_entry"], "text": text}

    # -- internal ----------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()


def _compact(d: dict) -> dict:
    """Remove None values from a dict."""
    return {k: v for k, v in d.items() if v is not None}
