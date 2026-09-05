"""Tests for marketplace partner API keys."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.marketplace import MarketplaceIntegrationConnection, MarketplacePartnerApiKey
from app.services.partner_api_keys import (
    generate_partner_api_key,
    hash_partner_api_key,
    serialize_partner_api_key,
    validate_partner_api_key,
    verify_partner_api_key,
)


def test_generate_and_verify_partner_api_key_hash():
    raw = generate_partner_api_key()
    stored = hash_partner_api_key(raw)
    assert raw.startswith("r4r_live_")
    assert verify_partner_api_key(raw, stored)
    assert not verify_partner_api_key(raw + "tampered", stored)


def test_validate_partner_api_key_accepts_active_key():
    raw = generate_partner_api_key()
    connection_id = uuid.uuid4()
    team_id = uuid.uuid4()
    row = MarketplacePartnerApiKey(
        id=uuid.uuid4(),
        connection_id=connection_id,
        team_id=team_id,
        name="Production key",
        key_prefix=raw[:16],
        key_hash=hash_partner_api_key(raw),
        status="active",
        allowed_scopes=["humanoid:read"],
    )
    connection = MarketplaceIntegrationConnection(
        id=connection_id,
        team_id=team_id,
        connection_type="mcp_server",
        name="Acme MCP",
        status="active",
        allowed_scopes=["humanoid:read", "leads:read"],
    )

    key_query = MagicMock()
    key_query.filter.return_value.all.return_value = [row]
    conn_query = MagicMock()
    conn_query.filter.return_value.first.return_value = connection

    def query_side_effect(model):
        if model is MarketplacePartnerApiKey:
            return key_query
        if model is MarketplaceIntegrationConnection:
            return conn_query
        return MagicMock()

    db = MagicMock()
    db.query.side_effect = query_side_effect

    ctx = validate_partner_api_key(db, raw)
    assert ctx is not None
    assert ctx.connection_id == connection_id
    assert ctx.connection_name == "Acme MCP"
    assert "humanoid:read" in ctx.allowed_scopes
    db.commit.assert_called_once()


def test_validate_partner_api_key_rejects_revoked_status():
    raw = generate_partner_api_key()
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    assert validate_partner_api_key(db, raw) is None


def test_serializer_never_returns_hash():
    row = MarketplacePartnerApiKey(
        id=uuid.uuid4(),
        connection_id=uuid.uuid4(),
        team_id=uuid.uuid4(),
        name="UI key",
        key_prefix="r4r_live_abcd12",
        key_hash=hash_partner_api_key(generate_partner_api_key()),
        status="active",
        allowed_scopes=["leads:read"],
        created_at=datetime.now(timezone.utc),
    )
    out = serialize_partner_api_key(row)
    assert out["keyPrefix"] == "r4r_live_abcd12"
    assert "keyHash" not in out
    assert out["status"] == "active"
