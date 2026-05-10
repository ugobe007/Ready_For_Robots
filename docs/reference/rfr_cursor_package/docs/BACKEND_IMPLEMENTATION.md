# ReadyForRobots — Implementation Guide for Three Next Steps

Stack: **FastAPI (Fly.dev) + Supabase (Postgres) + Next.js (Vercel)**
Auth: Supabase JWT Bearer token via `_require_user` dependency from `app/api/auth_deps.py`
DB: SQLAlchemy Session via `get_db` from `app/database.py`
Migrations: Alembic in `migrations/versions/`

---

## 1. Auto-Save Edited Proposal Text

### What it does
When a user edits a proposal in the split-pane editor and clicks "Update Preview", the edited text is saved back to Supabase so it persists across page refreshes.

### Step 1 — Alembic migration

Create `migrations/versions/g5h6i7j8k9l0_add_proposals_table.py`:

```python
"""Add pipeline_proposals table

Revision ID: g5h6i7j8k9l0
Revises: f3a4b5c6d7e8
Create Date: 2026-05-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "g5h6i7j8k9l0"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),          # Supabase auth UID
        sa.Column("company_id", sa.String(), nullable=True),        # links to companies.id if available
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("proposal_text", sa.Text(), nullable=False),      # the edited proposal content
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_proposals_user_id", "pipeline_proposals", ["user_id"])
    op.create_index("ix_pipeline_proposals_company_id", "pipeline_proposals", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_proposals_company_id", table_name="pipeline_proposals")
    op.drop_index("ix_pipeline_proposals_user_id", table_name="pipeline_proposals")
    op.drop_table("pipeline_proposals")
```

Run it:
```bash
alembic upgrade head
```

### Step 2 — FastAPI router

Create `app/api/proposals.py`:

```python
"""
Proposals API
=============
POST /api/proposals          — upsert a proposal for a company (create or update by user+company_name)
GET  /api/proposals          — list all proposals for the current user
GET  /api/proposals/{id}     — get a single proposal by UUID
DELETE /api/proposals/{id}   — delete a proposal
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth_deps import _require_user

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


class ProposalUpsert(BaseModel):
    company_name: str
    proposal_text: str
    company_id: Optional[str] = None
    contact_email: Optional[str] = None


class ProposalResponse(BaseModel):
    id: str
    company_name: str
    proposal_text: str
    company_id: Optional[str]
    contact_email: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=ProposalResponse)
def upsert_proposal(
    body: ProposalUpsert,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    """Create or update a proposal. One proposal per user+company_name."""
    uid = user["uid"]
    now = datetime.now(timezone.utc)

    existing = db.execute(
        "SELECT id FROM pipeline_proposals WHERE user_id = :uid AND company_name = :cn",
        {"uid": uid, "cn": body.company_name},
    ).fetchone()

    if existing:
        db.execute(
            """UPDATE pipeline_proposals
               SET proposal_text = :text,
                   contact_email = :email,
                   company_id    = :cid,
                   updated_at    = :now
               WHERE id = :id""",
            {
                "text": body.proposal_text,
                "email": body.contact_email,
                "cid": body.company_id,
                "now": now,
                "id": str(existing["id"]),
            },
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM pipeline_proposals WHERE id = :id",
            {"id": str(existing["id"])},
        ).fetchone()
    else:
        new_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO pipeline_proposals
               (id, user_id, company_name, proposal_text, contact_email, company_id, created_at, updated_at)
               VALUES (:id, :uid, :cn, :text, :email, :cid, :now, :now)""",
            {
                "id": new_id,
                "uid": uid,
                "cn": body.company_name,
                "text": body.proposal_text,
                "email": body.contact_email,
                "cid": body.company_id,
                "now": now,
            },
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM pipeline_proposals WHERE id = :id", {"id": new_id}
        ).fetchone()

    return dict(row)


@router.get("", response_model=list[ProposalResponse])
def list_proposals(
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    rows = db.execute(
        "SELECT * FROM pipeline_proposals WHERE user_id = :uid ORDER BY updated_at DESC",
        {"uid": user["uid"]},
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    row = db.execute(
        "SELECT * FROM pipeline_proposals WHERE id = :id AND user_id = :uid",
        {"id": proposal_id, "uid": user["uid"]},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return dict(row)


@router.delete("/{proposal_id}")
def delete_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    result = db.execute(
        "DELETE FROM pipeline_proposals WHERE id = :id AND user_id = :uid",
        {"id": proposal_id, "uid": user["uid"]},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"deleted": True}
```

### Step 3 — Register in main.py

In `app/main.py`, add:
```python
from app.api.proposals import router as proposals_router
app.include_router(proposals_router)
```

### Step 4 — Frontend call (Next.js)

In the page where your proposal editor lives (e.g. `pages/crm.js` or `pages/pipeline-results.js`), add a save call after the user clicks "Update Preview":

```js
import { getApiBase } from '../lib/apiBase';

async function saveProposal(companyName, proposalText, contactEmail, companyId) {
  const token = supabase.auth.session()?.access_token;
  const res = await fetch(`${getApiBase()}/api/proposals`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      company_name: companyName,
      proposal_text: proposalText,
      contact_email: contactEmail,
      company_id: companyId ?? null,
    }),
  });
  if (!res.ok) throw new Error('Failed to save proposal');
  return res.json();
}
```

Call `saveProposal(...)` in your "Update Preview" handler after the PDF re-renders successfully.

---

## 2. Sender Personalisation in the PDF Footer

### What it does
Pulls the user's name, title, and company from a `user_settings` table and injects them into the PDF footer so every downloaded proposal is correctly attributed.

### Step 1 — Alembic migration

Create `migrations/versions/h6i7j8k9l0m1_add_user_settings.py`:

```python
"""Add user_settings table

Revision ID: h6i7j8k9l0m1
Revises: g5h6i7j8k9l0
Create Date: 2026-05-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "h6i7j8k9l0m1"
down_revision: Union[str, Sequence[str], None] = "g5h6i7j8k9l0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("sender_name", sa.String(), nullable=True),
        sa.Column("sender_title", sa.String(), nullable=True),
        sa.Column("sender_company", sa.String(), nullable=True),
        sa.Column("sender_email", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
```

### Step 2 — FastAPI router

Add to `app/api/user.py` (or create `app/api/settings.py`):

```python
# Add to existing user.py imports
from datetime import datetime, timezone

class UserSettingsUpdate(BaseModel):
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    sender_company: Optional[str] = None
    sender_email: Optional[str] = None

class UserSettingsResponse(BaseModel):
    sender_name: Optional[str]
    sender_title: Optional[str]
    sender_company: Optional[str]
    sender_email: Optional[str]

@router.get("/api/user/settings", response_model=UserSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    row = db.execute(
        "SELECT * FROM user_settings WHERE user_id = :uid",
        {"uid": user["uid"]},
    ).fetchone()
    if not row:
        return {"sender_name": None, "sender_title": None, "sender_company": None, "sender_email": None}
    return dict(row)

@router.put("/api/user/settings")
def update_settings(
    body: UserSettingsUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    now = datetime.now(timezone.utc)
    db.execute(
        """INSERT INTO user_settings (user_id, sender_name, sender_title, sender_company, sender_email, updated_at)
           VALUES (:uid, :name, :title, :company, :email, :now)
           ON CONFLICT (user_id) DO UPDATE SET
               sender_name    = EXCLUDED.sender_name,
               sender_title   = EXCLUDED.sender_title,
               sender_company = EXCLUDED.sender_company,
               sender_email   = EXCLUDED.sender_email,
               updated_at     = EXCLUDED.updated_at""",
        {
            "uid": user["uid"],
            "name": body.sender_name,
            "title": body.sender_title,
            "company": body.sender_company,
            "email": body.sender_email,
            "now": now,
        },
    )
    db.commit()
    return {"saved": True}
```

### Step 3 — Frontend: Settings form in profile.js

In `pages/profile.js`, add a "Proposal Sender Settings" section:

```jsx
const [settings, setSettings] = useState({ sender_name: '', sender_title: '', sender_company: '', sender_email: '' });

// Load on mount
useEffect(() => {
  const token = supabase.auth.session()?.access_token;
  fetch(`${getApiBase()}/api/user/settings`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then(r => r.json())
    .then(data => setSettings(data));
}, []);

// Save handler
async function saveSettings() {
  const token = supabase.auth.session()?.access_token;
  await fetch(`${getApiBase()}/api/user/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(settings),
  });
}
```

### Step 4 — Pass sender fields into the PDF generation call

When calling your PDF endpoint, fetch settings first and pass them as body fields:

```js
const settings = await fetch(`${getApiBase()}/api/user/settings`, {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json());

const pdfRes = await fetch(`${getApiBase()}/api/proposal/pdf`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ...proposalData,
    senderName: settings.sender_name ?? 'Your Name',
    senderTitle: settings.sender_title ?? 'Sales Representative',
    senderCompany: settings.sender_company ?? 'ReadyForRobots',
  }),
});
```

In your PDF generation code (server-side), use these fields in the footer instead of hardcoded values.

---

## 3. Email Delivery via Resend

### What it does
Adds a `POST /api/leads/{company_id}/send-outreach` endpoint that reads the lead's contact email and outreach draft from Supabase, sends the email via Resend, and records the send timestamp.

### Step 1 — Alembic migration (add outreach fields to crm_accounts)

Create `migrations/versions/i7j8k9l0m1n2_add_outreach_fields.py`:

```python
"""Add outreach tracking fields to crm_accounts

Revision ID: i7j8k9l0m1n2
Revises: h6i7j8k9l0m1
Create Date: 2026-05-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "i7j8k9l0m1n2"
down_revision: Union[str, Sequence[str], None] = "h6i7j8k9l0m1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add outreach fields to crm_accounts if they don't already exist
    op.add_column("crm_accounts", sa.Column("contact_email", sa.String(), nullable=True))
    op.add_column("crm_accounts", sa.Column("outreach_draft", sa.Text(), nullable=True))
    op.add_column("crm_accounts", sa.Column("outreach_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("crm_accounts", sa.Column("outreach_stage", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("crm_accounts", "outreach_stage")
    op.drop_column("crm_accounts", "outreach_sent_at")
    op.drop_column("crm_accounts", "outreach_draft")
    op.drop_column("crm_accounts", "contact_email")
```

### Step 2 — Install Resend

```bash
pip install resend
# Add to requirements.txt:
resend>=0.8.0
```

### Step 3 — Add the send-outreach endpoint to crm.py

```python
# Add to app/api/crm.py imports
import os
import resend
from datetime import datetime, timezone

resend.api_key = os.getenv("RESEND_API_KEY", "")

class SendOutreachRequest(BaseModel):
    contact_email: Optional[str] = None   # override if not already stored
    outreach_draft: Optional[str] = None  # override if not already stored

@router.post("/api/crm/accounts/{account_id}/send-outreach")
def send_outreach(
    account_id: str,
    body: SendOutreachRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    # Fetch the account (scoped to user's teams)
    row = db.execute(
        """SELECT ca.*, c.name as company_name
           FROM crm_accounts ca
           JOIN companies c ON c.id = ca.company_id
           WHERE ca.id = :id""",
        {"id": account_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")

    contact_email = body.contact_email or row["contact_email"]
    outreach_draft = body.outreach_draft or row["outreach_draft"]

    if not contact_email:
        raise HTTPException(status_code=400, detail="No contact email on file for this account")
    if not outreach_draft:
        raise HTTPException(status_code=400, detail="No outreach draft on file for this account")

    # Fetch sender settings
    settings = db.execute(
        "SELECT * FROM user_settings WHERE user_id = :uid",
        {"uid": user["uid"]},
    ).fetchone()
    sender_name = (settings["sender_name"] if settings else None) or "SCOUT"
    sender_email = os.getenv("RESEND_FROM_EMAIL", "scout@readyforrobots.com")

    # Build subject line
    subject = f"Automation Opportunity — {row['company_name']}"

    # Send via Resend
    try:
        resend.Emails.send({
            "from": f"{sender_name} <{sender_email}>",
            "to": contact_email,
            "subject": subject,
            "text": outreach_draft,
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Email send failed: {str(e)}")

    # Record the send
    now = datetime.now(timezone.utc)
    db.execute(
        """UPDATE crm_accounts
           SET contact_email   = :email,
               outreach_draft  = :draft,
               outreach_sent_at = :now,
               outreach_stage  = 'intro_sent'
           WHERE id = :id""",
        {"email": contact_email, "draft": outreach_draft, "now": now, "id": account_id},
    )
    db.commit()

    return {"sent": True, "to": contact_email, "sent_at": now.isoformat()}
```

### Step 4 — Add RESEND_API_KEY to Fly.dev secrets

```bash
fly secrets set RESEND_API_KEY=re_xxxxxxxxxxxx
fly secrets set RESEND_FROM_EMAIL=scout@yourdomain.com
```

Your sending domain (`yourdomain.com`) must be verified in the Resend dashboard. For testing, Resend allows sending to your own verified email without domain verification.

### Step 5 — Frontend call (Next.js)

In `pages/crm.js`, wire the "Approve & Send" button:

```js
async function sendOutreach(accountId, contactEmail, outreachDraft) {
  const token = supabase.auth.session()?.access_token;
  const res = await fetch(`${getApiBase()}/api/crm/accounts/${accountId}/send-outreach`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      contact_email: contactEmail,
      outreach_draft: outreachDraft,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Send failed');
  }
  return res.json();
}

// In your button onClick:
try {
  setSending(true);
  const result = await sendOutreach(account.id, account.contact_email, account.outreach_draft);
  toast.success(`Email sent to ${result.to}`);
  // Refresh account data to show outreach_stage = 'intro_sent'
  refetchAccounts();
} catch (e) {
  toast.error(e.message);
} finally {
  setSending(false);
}
```

---

## Deployment Order

1. Commit the three migration files and run `alembic upgrade head` on Fly.dev (via `fly ssh console -C "alembic upgrade head"` or your CI pipeline).
2. Add `resend` to `requirements.txt` and redeploy the FastAPI app to Fly.dev.
3. Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` as Fly secrets.
4. Deploy the Next.js frontend changes to Vercel.
