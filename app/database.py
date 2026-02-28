import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_raw_url = os.getenv("DATABASE_URL", "sqlite:///./ready_for_robots.db")

# Supabase (and some PaaS providers) emit postgres:// which SQLAlchemy 1.4+
# requires to be postgresql+psycopg2://  — normalise it here.
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

DATABASE_URL = _raw_url

if "postgresql" in DATABASE_URL:
    # Supabase connection-pooler settings (Supavisor / PgBouncer)
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,       # recycle stale connections
        pool_recycle=300,         # recycle every 5 min (Supabase closes idle at 60s)
    )
else:
    # SQLite local dev fallback
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()