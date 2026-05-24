import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root is on path (for app.* imports when run via alembic CLI)
_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from app.env_loader import database_url_is_template_or_sqlite

# Same load order as app/database.py so Alembic uses the same DATABASE_URL as the app.
_env_database_url = (os.environ.get("DATABASE_URL") or "").strip()
load_dotenv(Path(_src) / "frontend" / "nextjs" / ".env.local")
load_dotenv(Path(_src) / ".env", override=True)
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded_from_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _env_database_url and database_url_is_template_or_sqlite(_loaded_from_dotenv):
    os.environ["DATABASE_URL"] = _env_database_url

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# DATABASE_URL from environment or .env; normalize for psycopg2 + Supabase SSL
_db_url = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")
if _db_url:
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif _db_url.startswith("postgresql://") and not _db_url.startswith("postgresql+"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "supabase.co" in _db_url and "sslmode=" not in _db_url:
        sep = "&" if "?" in _db_url else "?"
        _db_url = f"{_db_url}{sep}sslmode=require"
    config.set_main_option("sqlalchemy.url", _db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.database import Base
import app.models
import app.models.robot_company
import app.models.shared_calculation
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"connect_timeout": 10},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
