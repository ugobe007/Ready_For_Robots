"""Add detected_intent + sentiment to outreach replies.

Reply understanding for the communication learning loop: the inbound webhook
classifies each reply (interested / meeting / pricing / not_now / already_tried /
not_a_fit / referral / unsubscribe / auto_reply) and stores a coarse sentiment.
This lets the weekly learning report attribute outcomes back to the trust-first
angle (payload.variant_id) that produced the send.

Revision ID: t4u5v6w7x8y9
Revises: s3t4u5v6w7x8
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "t4u5v6w7x8y9"
down_revision: Union[str, Sequence[str], None] = "s3t4u5v6w7x8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "outreach_replies",
        sa.Column("detected_intent", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "outreach_replies",
        sa.Column("sentiment", sa.String(length=16), nullable=True),
    )
    op.create_index(
        "ix_outreach_replies_detected_intent",
        "outreach_replies",
        ["detected_intent"],
    )


def downgrade() -> None:
    op.drop_index("ix_outreach_replies_detected_intent", table_name="outreach_replies")
    op.drop_column("outreach_replies", "sentiment")
    op.drop_column("outreach_replies", "detected_intent")
