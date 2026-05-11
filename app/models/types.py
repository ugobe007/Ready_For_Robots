"""Portable SQLAlchemy column types for production Postgres and SQLite tests."""

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

JSONB = PostgresJSONB().with_variant(JSON(), "sqlite")


def UUID(as_uuid: bool = True):
    return PostgresUUID(as_uuid=as_uuid).with_variant(String(36), "sqlite")
