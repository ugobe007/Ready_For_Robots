"""SPA catch-all must not answer unknown /api/* as index.html.

When Fly is behind the frontend, GET /api/robot-jobs/preview used to return
the Vite shell with HTTP 200. The home job board then parsed HTML as an
empty table: “No named-employer jobs in the live table yet.”
"""
from __future__ import annotations


def is_api_catchall_path(full_path: str) -> bool:
    path = (full_path or "").split("?", 1)[0].lstrip("/")
    return path == "api" or path.startswith("api/")
