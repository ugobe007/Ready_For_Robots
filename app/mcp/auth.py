"""MCP HTTP authentication — global bearer + per-partner marketplace keys."""
from __future__ import annotations

from typing import Optional

from starlette.requests import Request

from app.database import SessionLocal
from app.mcp.config import mcp_bearer_token
from app.services.partner_api_keys import PartnerApiKeyContext, validate_partner_api_key


def extract_mcp_credential(request: Request) -> str:
    header = (request.headers.get("authorization") or "").strip()
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return (request.headers.get("x-r4r-api-key") or request.headers.get("X-R4R-API-Key") or "").strip()


def authenticate_mcp_request(request: Request) -> tuple[bool, Optional[PartnerApiKeyContext]]:
    credential = extract_mcp_credential(request)
    if not credential:
        return False, None

    required = mcp_bearer_token()
    if required and credential == required:
        return True, None

    db = SessionLocal()
    try:
        partner = validate_partner_api_key(db, credential)
        if partner:
            return True, partner
    finally:
        db.close()

    return False, None
