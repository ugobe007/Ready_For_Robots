"""HTTP client for the Ready For Robots REST API."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from app.mcp.config import api_base_url, partner_api_key

DEFAULT_TIMEOUT = 45.0
MAX_RESPONSE_CHARS = 14_000


class R4RApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class R4RClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = (base_url or api_base_url()).rstrip("/")
        self.api_key = api_key if api_key is not None else partner_api_key()
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "readyforrobots-mcp/1.0",
        }
        if self.api_key:
            headers["X-R4R-API-Key"] = self.api_key
        return headers

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params or {}, headers=self._headers())
        return self._parse(response)

    async def post(
        self,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=json_body,
                params=params or {},
                headers=self._headers(),
            )
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> Any:
        if response.status_code >= 400:
            detail = response.text[:500] or response.reason_phrase
            raise R4RApiError(response.status_code, detail)
        if not response.content:
            return {}
        return response.json()


def format_json(data: Any, max_chars: int = MAX_RESPONSE_CHARS) -> str:
    text = json.dumps(data, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...(truncated)"


_default_client: Optional[R4RClient] = None


def get_client() -> R4RClient:
    global _default_client
    if _default_client is None:
        _default_client = R4RClient()
    return _default_client
