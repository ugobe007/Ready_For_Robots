"""Pure helpers for DATABASE_URL / dotenv (no imports from app.database — no side effects)."""

from __future__ import annotations

from urllib.parse import urlparse

_PLACEHOLDER_PG_HOSTS = frozenset(
    {
        "host",
        "hostname",
        "your-host",
        "your_host",
        "db.host",
        "db.example.com",
    }
)


def database_url_is_template_or_sqlite(url: str) -> bool:
    """
    True if this URL should not win over a shell-exported DATABASE_URL.
    Used so a stale `export DATABASE_URL=...` does not overwrite a real .env after
    the user updates the password in the file.
    """
    s = (url or "").strip().strip('"').strip("'")
    if not s:
        return True
    if s.startswith("sqlite:"):
        return True
    # Copied from .env.example placeholders
    if "YOUR_PASSWORD" in s or "YOUR_PROJECT_REF" in s:
        return True
    if "postgresql" not in s and not s.startswith("postgres://"):
        return True
    u = s.replace("postgresql+psycopg2://", "postgresql://", 1)
    try:
        parsed = urlparse(u)
    except Exception:
        return True
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return True
    if host in _PLACEHOLDER_PG_HOSTS:
        return True
    if "...." in host:
        return True
    return False
