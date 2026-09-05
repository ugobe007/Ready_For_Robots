"""
LinkedIn company page integration — OAuth connect + publish.

Ready For Robots page: https://www.linkedin.com/company/114404417/admin/dashboard/
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.admin_auth import require_admin_jwt_or_key
from app.database import get_db
from app.services.linkedin_oauth import (
    LinkedInError,
    build_authorization_url,
    complete_oauth_callback,
    connection_status,
    is_configured,
    publish_organization_post,
)

router = APIRouter()


class LinkedInPublishIn(BaseModel):
    commentary: str = Field(..., min_length=1, max_length=3000)
    article_url: Optional[str] = None


@router.get("/status")
def linkedin_status(db: Session = Depends(get_db)):
    """Connection status for Content Studio / admin."""
    return connection_status(db)


@router.get("/connect")
def linkedin_connect(
    return_to: str = Query("", description="Frontend URL to redirect after OAuth"),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin_jwt_or_key),
):
    """Start OAuth — admin session or X-Admin-Key. Redirects to LinkedIn authorization."""
    if not is_configured():
        raise HTTPException(
            status_code=503,
            detail="Set LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, and LINKEDIN_REDIRECT_URI on the API server",
        )
    try:
        auth_url, _ = build_authorization_url(db, return_to=return_to)
    except LinkedInError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/connect-url")
def linkedin_connect_url(
    return_to: str = Query("", description="Frontend URL to redirect after OAuth"),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin_jwt_or_key),
):
    """Return OAuth URL as JSON (for SPA redirect). Admin session or X-Admin-Key."""
    if not is_configured():
        raise HTTPException(status_code=503, detail="LinkedIn app credentials not configured")
    try:
        auth_url, _ = build_authorization_url(db, return_to=return_to)
    except LinkedInError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"auth_url": auth_url}


@router.get("/callback")
def linkedin_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """OAuth callback from LinkedIn — stores tokens and redirects back to Content Studio."""
    if error:
        msg = error_description or error
        target = f"https://readyforrobots.com/social?linkedin=error&detail={quote(msg[:180])}"
        return RedirectResponse(url=target, status_code=302)

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    try:
        result = complete_oauth_callback(db, code=code, state=state)
    except LinkedInError as exc:
        target = f"https://readyforrobots.com/social?linkedin=error&detail={quote(str(exc)[:180])}"
        return RedirectResponse(url=target, status_code=302)

    return_to = (result.get("return_to") or "https://readyforrobots.com/social").strip()
    sep = "&" if "?" in return_to else "?"
    return RedirectResponse(url=f"{return_to}{sep}linkedin=connected", status_code=302)


@router.post("/publish")
def linkedin_publish(
    body: LinkedInPublishIn,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin_jwt_or_key),
):
    """Publish text to LinkedIn — admin session or X-Admin-Key."""
    try:
        return publish_organization_post(db, commentary=body.commentary, article_url=body.article_url)
    except LinkedInError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
