import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load repo-root .env, then Next.js .env.local (override) — same order as migrations/env.py
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / ".env")
load_dotenv(_root / "frontend" / "nextjs" / ".env.local", override=True)

_raw_url = os.getenv("DATABASE_URL", "sqlite:///./ready_for_robots.db")
_raw_url = (_raw_url or "").strip().strip('"').strip("'")
# Fly secrets must be a full URI — not a host, not base64. Otherwise we fall through to SQLite and APIs 500.
if _raw_url and not (
    _raw_url.startswith("postgres://")
    or _raw_url.startswith("postgresql://")
    or _raw_url.startswith("postgresql+")
    or _raw_url.startswith("sqlite:")
):
    print(
        "ERROR: DATABASE_URL must start with postgresql:// or postgres:// (or sqlite:). "
        "Copy the full connection string from Supabase → Database (URI). "
        "Falling back to local SQLite; production APIs will fail.",
        file=sys.stderr,
    )
    _raw_url = "sqlite:///./ready_for_robots.db"
if _raw_url and _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _raw_url and _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

DATABASE_URL = _raw_url or "sqlite:///./ready_for_robots.db"


def _ensure_pg_sslmode(url: str) -> str:
    """Supabase direct connections require SSL; pooler often does too."""
    if not url or "postgresql" not in url or "sqlite" in url:
        return url
    if "sslmode=" in url:
        return url
    if "supabase.co" not in url and "supabase.com" not in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}sslmode=require"


DATABASE_URL = _ensure_pg_sslmode(DATABASE_URL)

# Literal "HOST" / docs examples — DNS fails with "could not translate host name \"HOST\""
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


def _postgres_url_has_placeholder_host(url: str) -> bool:
    if not url or "postgresql" not in url:
        return False
    host = (urlparse(url).hostname or "").strip().lower()
    if not host:
        return True
    return host in _PLACEHOLDER_PG_HOSTS


if DATABASE_URL and "postgresql" in DATABASE_URL and _postgres_url_has_placeholder_host(DATABASE_URL):
    print(
        "WARNING: DATABASE_URL looks like a template (hostname is a placeholder, e.g. HOST). "
        "Set the real Supabase host (db.xxxxx.supabase.co) in .env or use sqlite:///./ready_for_robots.db. "
        "Falling back to local SQLite.",
        file=sys.stderr,
    )
    DATABASE_URL = "sqlite:///./ready_for_robots.db"

# Fly.io / many cloud hosts cannot reach Supabase *direct* DB (db.*.supabase.co:5432) reliably
# (IPv6 / routing → "connection refused"). Use the Transaction pooler URI on port 6543 from the
# Supabase dashboard: Settings → Database → Connection pooling.
if os.getenv("FLY_APP_NAME") and DATABASE_URL and "postgresql" in DATABASE_URL:
    _pr = urlparse(DATABASE_URL)
    _h = (_pr.hostname or "").lower()
    _p = _pr.port or 5432
    if _h.endswith(".supabase.co") and _h.startswith("db.") and _p == 5432:
        print(
            "WARNING: DATABASE_URL uses Supabase direct port 5432. On Fly.io this often fails with "
            "connection refused. Set DATABASE_URL to the Transaction pooler string (port 6543, "
            "user postgres.PROJECT_REF, host aws-0-REGION.pooler.supabase.com) from the Supabase dashboard.",
            file=sys.stderr,
        )


def _postgres_engine_kwargs(url: str) -> dict:
    """
    Supabase *session* pooler (pooler.*.supabase.com:5432) caps concurrent clients per project
    (FATAL: MaxClientsInSessionMode). Multiple Fly machines × a large SQLAlchemy pool exhausts it.
    Prefer Transaction pooler (:6543, user postgres.PROJECT_REF) for app servers.
    """
    base = {
        "pool_timeout": 30,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if not url or "postgresql" not in url or "sqlite" in url:
        return {**base, "pool_size": 5, "max_overflow": 10}
    pr = urlparse(url)
    host = (pr.hostname or "").lower()
    port = pr.port or 5432
    if "pooler.supabase.com" in host and port == 5432:
        print(
            "WARNING: DATABASE_URL uses Supabase Session pooler (:5432). Slots are very limited; "
            "switch to Transaction pooler (port 6543, user postgres.PROJECT_REF) in "
            "Supabase → Database → Connection string → Transaction mode to avoid 500s under load.",
            file=sys.stderr,
        )
        # Keep total connections small per process (multiple machines/workers add up).
        return {**base, "pool_size": 2, "max_overflow": 2}
    return {**base, "pool_size": 5, "max_overflow": 10}


try:
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        engine = create_engine(DATABASE_URL, **_postgres_engine_kwargs(DATABASE_URL))
    else:
        # Respect DATABASE_URL for SQLite (e.g. sqlite:///./ready_for_robots.db or absolute path)
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
except Exception as e:
    print(f"WARNING: DATABASE_URL invalid ({e}), using SQLite fallback. DB features may not work.", file=sys.stderr)
    engine = create_engine("sqlite:///./ready_for_robots.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()