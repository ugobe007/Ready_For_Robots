"""Canonical-URL robot ledger, research stamps, presentation queue, apply meeting URL.

Revision ID: jruc0a1b2c3d4
Revises: edcl0a1b2c3d4
"""
from typing import Sequence, Union
from urllib.parse import urlparse, urlunparse

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "jruc0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "edcl0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _canonical(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    if "://" not in text:
        text = f"https://{text}"
    try:
        parsed = urlparse(text)
    except Exception:
        return text[:2000]
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host:
        return text[:2000]
    path = (parsed.path or "").rstrip("/")
    netloc = host
    if parsed.port and parsed.port not in {80, 443}:
        netloc = f"{host}:{parsed.port}"
    scheme = (parsed.scheme or "https").lower()
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))[:2000]


def upgrade() -> None:
    op.add_column("robot_submissions", sa.Column("canonical_url", sa.Text(), nullable=True))
    op.add_column("robot_submissions", sa.Column("host", sa.String(length=240), nullable=True))
    op.add_column("robot_submissions", sa.Column("last_researched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "robot_submissions",
        sa.Column("research_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "robot_submissions",
        sa.Column("research_snippets", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
    )

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, submitted_url, website_domain FROM robot_submissions")).fetchall()
    for row in rows:
        canon = _canonical(row.submitted_url) or (row.submitted_url or "")[:2000]
        host = urlparse(canon).hostname or (row.website_domain or "")[:240]
        bind.execute(
            sa.text(
                "UPDATE robot_submissions SET canonical_url = :c, host = :h WHERE id = :id"
            ),
            {"c": canon, "h": host[:240], "id": row.id},
        )

    inspector = sa.inspect(bind)
    unique_names = {u.get("name") for u in inspector.get_unique_constraints("robot_submissions")}
    for name in ("uq_robot_submissions_website_domain", "robot_submissions_website_domain_key"):
        if name in unique_names:
            op.drop_constraint(name, "robot_submissions", type_="unique")

    op.create_unique_constraint(
        "uq_robot_submissions_canonical_url",
        "robot_submissions",
        ["canonical_url"],
    )
    op.create_index("ix_robot_submissions_canonical_url", "robot_submissions", ["canonical_url"])
    op.create_index("ix_robot_submissions_host", "robot_submissions", ["host"])
    op.create_index(
        "ix_robot_submissions_last_researched_at",
        "robot_submissions",
        ["last_researched_at"],
    )
    op.create_index(
        "ix_robot_submissions_research_status",
        "robot_submissions",
        ["research_status"],
    )

    op.add_column("job_applications", sa.Column("meeting_url", sa.Text(), nullable=True))

    op.create_table(
        "robot_presentation_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("submitted_url", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(length=240), nullable=True),
        sa.Column("product_name", sa.String(length=240), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("provider_job_id", sa.String(length=160), nullable=True),
        sa.Column("deck_url", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("paid", sa.String(length=8), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_robot_presentation_requests_canonical_url",
        "robot_presentation_requests",
        ["canonical_url"],
    )
    op.create_index(
        "ix_robot_presentation_requests_user_id",
        "robot_presentation_requests",
        ["user_id"],
    )
    op.create_index(
        "ix_robot_presentation_requests_status",
        "robot_presentation_requests",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_robot_presentation_requests_status", table_name="robot_presentation_requests")
    op.drop_index("ix_robot_presentation_requests_user_id", table_name="robot_presentation_requests")
    op.drop_index(
        "ix_robot_presentation_requests_canonical_url",
        table_name="robot_presentation_requests",
    )
    op.drop_table("robot_presentation_requests")
    op.drop_column("job_applications", "meeting_url")
    op.drop_index("ix_robot_submissions_research_status", table_name="robot_submissions")
    op.drop_index("ix_robot_submissions_last_researched_at", table_name="robot_submissions")
    op.drop_index("ix_robot_submissions_host", table_name="robot_submissions")
    op.drop_index("ix_robot_submissions_canonical_url", table_name="robot_submissions")
    op.drop_constraint("uq_robot_submissions_canonical_url", "robot_submissions", type_="unique")
    op.drop_column("robot_submissions", "research_snippets")
    op.drop_column("robot_submissions", "research_status")
    op.drop_column("robot_submissions", "last_researched_at")
    op.drop_column("robot_submissions", "host")
    op.drop_column("robot_submissions", "canonical_url")
    op.create_unique_constraint(
        "uq_robot_submissions_website_domain",
        "robot_submissions",
        ["website_domain"],
    )
