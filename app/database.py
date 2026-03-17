import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_raw_url = os.getenv("DATABASE_URL", "sqlite:///./ready_for_robots.db")
_raw_url = (_raw_url or "").strip().strip('"').strip("'")
if _raw_url and _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _raw_url and _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

DATABASE_URL = _raw_url or "sqlite:///./ready_for_robots.db"

try:
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    else:
        engine = create_engine("sqlite:///./ready_for_robots.db", connect_args={"check_same_thread": False})
except Exception as e:
    import sys
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