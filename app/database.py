import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Load repo-root .env, then Next.js .env.local (override) so DATABASE_URL matches Alembic / local dev
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


def _prefer_ipv4_hostaddr_for_fly(url: str) -> str:
    """
    Fly.io outbound to db.*.supabase.co often picks IPv6 first; port 6543 then returns
    'Connection refused' (see fly logs: psycopg2 OperationalError to ... port 6543 failed).
    libpq can connect via IPv4 literal using hostaddr= while keeping host= for TLS name.
    """
    if not url or "sqlite" in url or "postgresql" not in url:
        return url
    if "hostaddr=" in url.lower():
        return url
    try:
        pr = urlparse(url)
        host = (pr.hostname or "").lower()
    except Exception:
        return url
    if not (host.startswith("db.") and host.endswith(".supabase.co")):
        return url
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        if not infos:
            print(
                f"WARNING: No IPv4 address for {host}; using default DNS (may use IPv6 on Fly).",
                file=sys.stderr,
            )
            return url
        ipv4 = infos[0][4][0]
    except OSError as e:
        print(f"WARNING: IPv4 resolve for {host} failed ({e}); not setting hostaddr.", file=sys.stderr)
        return url
    sep = "&" if "?" in url else "?"
    print(
        f"INFO: Fly.io + Supabase: using hostaddr={ipv4} for {host} (avoid IPv6 connection refused).",
        file=sys.stderr,
    )
    return f"{url}{sep}hostaddr={ipv4}"


if os.getenv("FLY_APP_NAME"):
    DATABASE_URL = _prefer_ipv4_hostaddr_for_fly(DATABASE_URL)

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

def _pg_connect_args(url: str) -> dict:
    """
    Extra libpq/psycopg2 options for cloud Postgres (esp. Supabase pooler from Fly.io).

    - connect_timeout: fail fast instead of hanging.
    - gssencmode=disable: avoids rare GSSAPI negotiation failures on Linux (Fly VMs).
    """
    args: dict = {"connect_timeout": 15}
    if "supabase" in url.lower():
        args["gssencmode"] = "disable"
    return args


def _pooler_disables_prepared_statements(url: str) -> bool:
    """Supabase transaction pooler (6543 / pooler.supabase.com) cannot use prepared statements."""
    if not url or "postgresql" not in url:
        return False
    u = url.lower()
    return "pooler.supabase.com" in u or ":6543" in url


def _register_pooler_psycopg2(engine, dsn_url: str) -> None:
    """Disable psycopg2 prepared statements for PgBouncer/Supavisor transaction pool (port 6543)."""
    if not _pooler_disables_prepared_statements(dsn_url):
        return

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, connection_record):
        # psycopg2: None disables prepared statements; 0 does NOT (see Connection.prepare_threshold docs).
        if hasattr(dbapi_conn, "prepare_threshold"):
            dbapi_conn.prepare_threshold = None


try:
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args=_pg_connect_args(DATABASE_URL),
        )
        _register_pooler_psycopg2(engine, DATABASE_URL)
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