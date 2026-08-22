"""Portable SQLAlchemy column types for production Postgres and SQLite tests."""
from __future__ import annotations

import uuid as uuid_mod

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import CHAR, TypeDecorator

JSONB = PostgresJSONB().with_variant(JSON(), "sqlite")


class GUID(TypeDecorator):
    """Postgres UUID, SQLite CHAR(36). Accepts uuid.UUID or str on bind."""

    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid: bool = True):
        super().__init__()
        self.as_uuid = as_uuid

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            if self.as_uuid:
                return value if isinstance(value, uuid_mod.UUID) else uuid_mod.UUID(str(value))
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if self.as_uuid:
            return value if isinstance(value, uuid_mod.UUID) else uuid_mod.UUID(str(value))
        return str(value)


def UUID(as_uuid: bool = True):
    return GUID(as_uuid=as_uuid)
