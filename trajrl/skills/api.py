"""HTTP client for the trajrl.com `/api/skills` endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://trajrl.com"
_TIMEOUT = 30.0


@dataclass
class SkillsClient:
    base_url: str = DEFAULT_BASE_URL
    _client: httpx.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=_TIMEOUT,
            headers={"Accept": "application/json"},
        )

    def list(
        self,
        *,
        query: str | None = None,
        tags: list[str] | None = None,
        agent: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """GET /api/skills with optional filters."""
        params: list[tuple[str, str]] = []
        if query:
            params.append(("q", query))
        if tags:
            for tag in tags:
                params.append(("tag", tag))
        if agent:
            params.append(("agent", agent))
        if page is not None:
            params.append(("page", str(page)))
        if limit is not None:
            params.append(("limit", str(limit)))
        return self._get("/api/skills", params=params or None)

    def show(self, slug: str) -> dict[str, Any]:
        """GET /api/skills/:slug — full skill payload including markdown content."""
        return self._get(f"/api/skills/{slug}")

    def tags(self) -> dict[str, Any]:
        """GET /api/skills/tags — tag → skill count."""
        return self._get("/api/skills/tags")

    def _get(self, path: str, params: Any | None = None) -> dict[str, Any]:
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()
