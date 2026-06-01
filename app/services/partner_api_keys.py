"""Per-partner API keys for marketplace MCP and REST integrations."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceIntegrationConnection, MarketplacePartnerApiKey

KEY_PREFIX = "r4r_live_"
KEY_PREFIX_DISPLAY_LEN = 16


@dataclass(frozen=True)
class PartnerApiKeyContext:
    key_id: UUID
    connection_id: UUID
    team_id: UUID
    connection_name: str
    allowed_scopes: tuple[str, ...]


def _pepper() -> str:
    return (os.getenv("R4R_API_KEY_PEPPER") or os.getenv("SECRET_KEY") or "ready-for-robots-dev-pepper").strip()


def hash_partner_api_key(raw_key: str) -> str:
    material = f"{_pepper()}:{raw_key}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def generate_partner_api_key() -> str:
    return f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"


def key_prefix_for(raw_key: str) -> str:
    return raw_key[:KEY_PREFIX_DISPLAY_LEN]


def verify_partner_api_key(raw_key: str, stored_hash: str) -> bool:
    expected = hash_partner_api_key(raw_key)
    return hmac.compare_digest(expected, stored_hash)


def create_partner_api_key(
    db: Session,
    *,
    connection: MarketplaceIntegrationConnection,
    created_by_user_id: Optional[UUID],
    name: str,
    allowed_scopes: Optional[List[str]] = None,
) -> tuple[MarketplacePartnerApiKey, str]:
    raw_key = generate_partner_api_key()
    scopes = allowed_scopes if allowed_scopes is not None else list(connection.allowed_scopes or [])
    row = MarketplacePartnerApiKey(
        connection_id=connection.id,
        team_id=connection.team_id,
        created_by_user_id=created_by_user_id,
        name=name.strip() or f"{connection.name} key",
        key_prefix=key_prefix_for(raw_key),
        key_hash=hash_partner_api_key(raw_key),
        status="active",
        allowed_scopes=scopes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, raw_key


def revoke_partner_api_key(db: Session, row: MarketplacePartnerApiKey) -> MarketplacePartnerApiKey:
    row.status = "revoked"
    row.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def validate_partner_api_key(db: Session, raw_key: str) -> Optional[PartnerApiKeyContext]:
    token = (raw_key or "").strip()
    if not token.startswith(KEY_PREFIX) or len(token) < 24:
        return None

    prefix = key_prefix_for(token)
    candidates = (
        db.query(MarketplacePartnerApiKey)
        .filter(
            MarketplacePartnerApiKey.key_prefix == prefix,
            MarketplacePartnerApiKey.status == "active",
        )
        .all()
    )
    now = datetime.now(timezone.utc)
    for row in candidates:
        if row.expires_at and row.expires_at <= now:
            continue
        if not verify_partner_api_key(token, row.key_hash):
            continue
        connection = (
            db.query(MarketplaceIntegrationConnection)
            .filter(MarketplaceIntegrationConnection.id == row.connection_id)
            .first()
        )
        if not connection or connection.status not in ("active", "draft"):
            continue
        row.last_used_at = now
        db.commit()
        scopes = row.allowed_scopes or connection.allowed_scopes or []
        return PartnerApiKeyContext(
            key_id=row.id,
            connection_id=row.connection_id,
            team_id=row.team_id,
            connection_name=connection.name,
            allowed_scopes=tuple(str(s) for s in scopes),
        )
    return None


def serialize_partner_api_key(row: MarketplacePartnerApiKey) -> dict:
    return {
        "id": str(row.id),
        "connectionId": str(row.connection_id),
        "teamId": str(row.team_id),
        "name": row.name,
        "keyPrefix": row.key_prefix,
        "status": row.status,
        "allowedScopes": row.allowed_scopes or [],
        "lastUsedAt": row.last_used_at.isoformat() if row.last_used_at else None,
        "expiresAt": row.expires_at.isoformat() if row.expires_at else None,
        "revokedAt": row.revoked_at.isoformat() if row.revoked_at else None,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }
