import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Next.js `.env.local` first, then repo-root `.env` with override so `DATABASE_URL`
# and other backend secrets in `.env` are not replaced by stale copies in `.env.local`.
# (Same order as migrations/env.py and DB scripts.)
# Shell-exported DATABASE_URL must win: override=True would otherwise replace `export`
# with a stale or template line from `.env` (e.g. aws-....pooler.supabase.com).
_env_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
# Git worktrees are separate directories: secrets often live only in the main clone's
# .env. Point here so the app and scripts use the same DATABASE_URL as that file:
#   export DOTENV_PATH=/path/to/main/Ready_For_Robots/.env
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
# Only restore a pre-import shell `export DATABASE_URL=...` when .env still has a
# template / SQLite — otherwise a stale shell export overwrites an updated .env
# (e.g. after password rotation → SASL authentication failed).
_loaded_from_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _env_database_url and database_url_is_template_or_sqlite(_loaded_from_dotenv):
    os.environ["DATABASE_URL"] = _env_database_url

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


def _warn_if_stale_supabase_direct_url(url: str) -> None:
    """
    Logs often show db.* + user postgres while the user believes they use Session pooler.
    Pooler URIs use *.pooler.supabase.com and user postgres.<project_ref>.
    Silence: export SUPABASE_ALLOW_DIRECT_DB=1
    """
    if os.getenv("SUPABASE_ALLOW_DIRECT_DB", "").strip().lower() in ("1", "true", "yes"):
        return
    if not url or "postgresql" not in url or "sqlite" in url:
        return
    try:
        u = urlparse(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    except Exception:
        return
    host = (u.hostname or "").lower()
    user = (u.username or "")
    port = u.port or 5432
    # Direct Postgres: db.*:5432 + user postgres. Transaction mode (dashboard) can be
    # db.*:6543 + user postgres — that is not "direct" and should not trigger this warning.
    if (
        host.startswith("db.")
        and "supabase.co" in host
        and user == "postgres"
        and port == 5432
    ):
        print(
            "WARNING: DATABASE_URL uses Supabase direct connection (db.*.supabase.co:5432, user postgres). "
            "For IPv4-only networks or Fly.io, the dashboard \"Transaction\" or \"Session pooler\" URI "
            "often works better. If you pasted Transaction pooler, use port 6543 on db.* or the "
            "*.pooler.supabase.com string from **Connect** — do not mix ports. "
            "If repo-root .env omits DATABASE_URL, a stale value in frontend/nextjs/.env.local or your shell may apply. "
            "Verify with: python3 scripts/check_db_connection.py. "
            "Suppress with SUPABASE_ALLOW_DIRECT_DB=1 if direct access is intentional.",
            file=sys.stderr,
        )


_warn_if_stale_supabase_direct_url(DATABASE_URL)

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
    u = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    host = (urlparse(u).hostname or "").strip().lower()
    if not host:
        return True
    if host in _PLACEHOLDER_PG_HOSTS:
        return True
    # Pasted abbreviated examples: aws-....pooler.supabase.com (invalid DNS — not a real host)
    if "...." in host:
        return True
    return False


if DATABASE_URL and "postgresql" in DATABASE_URL and _postgres_url_has_placeholder_host(DATABASE_URL):
    print(
        "WARNING: DATABASE_URL hostname is not a real database host (placeholder, HOST, or e.g. "
        "aws-....pooler.supabase.com with four dots). Copy the full URI from Supabase → Database → "
        "Connection string; the pooler host looks like aws-0-us-east-1.pooler.supabase.com "
        "(region + pool number, not ....). Falling back to local SQLite.",
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
            "WARNING: DATABASE_URL uses Supabase direct port 5432 on db.*. On Fly.io this often fails "
            "(IPv6 / routing). Set DATABASE_URL to the **Transaction** or **Session pooler** string "
            "from Supabase **Connect** (often port 6543 on db.* or pooler host — copy exactly).",
            file=sys.stderr,
        )


def _session_pooler_warning_suppressed() -> bool:
    """Set SUPABASE_SESSION_POOLER=1 when you intentionally use session mode (:5432 pooler)."""
    return os.getenv("SUPABASE_SESSION_POOLER", "").strip().lower() in ("1", "true", "yes")


def _postgres_engine_kwargs(url: str) -> dict:
    """
    Supabase session pooler (pooler.*.supabase.com:5432) caps concurrent clients per project
    (FATAL: MaxClientsInSessionMode). We use NullPool so connections are not hoarded idle.

    Transaction mode (:6543) allows more concurrent clients; use it if you outgrow session slots.
    Set SUPABASE_SESSION_POOLER=1 to silence the startup note when session mode is deliberate.
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
        if not _session_pooler_warning_suppressed():
            print(
                "NOTE: DATABASE_URL uses Supabase Session pooler (:5432 on *.pooler.supabase.com). "
                "Slots are limited project-wide; if you see MaxClientsInSessionMode / 500s under load, "
                "switch to Transaction mode from the dashboard (URI shape is in **Connect**) or set "
                "SUPABASE_SESSION_POOLER=1 to silence this.",
                file=sys.stderr,
            )
        # Session pooler caps *all* clients project-wide; a QueuePool holds idle conns and exhausts it.
        # NullPool opens a connection per request and closes when the session ends (no idle hoarding).
        return {"poolclass": NullPool, "pool_pre_ping": True}
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