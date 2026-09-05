# CRM schema migrations

## Source of truth

Schema changes for teams + CRM live in **Alembic**:

- `migrations/versions/c7d8e9f0a1b2_add_crm_teams_core.py`

**Supabase SQL editor:** use the plain SQL file (not the `.py` file):

- `migrations/sql/c7d8e9f0a1b2_add_crm_teams_core.sql`

Pasting the Python migration into the SQL editor will fail with a syntax error.

Revision chain: `62c6bf204268` → `3b95a4c9c416` → `a1b2c3d4e5f6` → **`c7d8e9f0a1b2` (head)**.

## Apply (Postgres / Supabase DB)

### 1. Set `DATABASE_URL` (not a placeholder)

Put it in the **repo-root** `.env` **or** in `frontend/nextjs/.env.local`. Alembic loads **both** (`.env` first, then `.env.local` overrides) so a valid URL in `.env.local` wins over an old `...@HOST...` line left in `.env`.

Use your **real** project directory (not `/path/to/...`). Put the URI in the repo-root **`.env`** as `DATABASE_URL=...`, or export it in the shell before running Alembic.

Supabase (example shape — **replace the password** with yours from **Project Settings → Database**):

```text
postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.lmoyydlhlgdyqbxkmkuz.supabase.co:6543/postgres
```

- Do **not** leave `[YOUR-PASSWORD]` or a hostname like `HOST` in the string — that causes `could not translate host name "HOST"`.
- If the password contains `@`, `:`, or `/`, **URL-encode** it (e.g. `@` → `%40`).
- **Port `6543`** is the pooler (often used on Fly). From your laptop, direct **`5432`** also works if your IP is allowed in Supabase **Database → Connection pooling / Network**.
- `migrations/env.py` loads **`.env`** automatically and appends `sslmode=require` for `supabase.co` hosts.

### 2. Run Alembic from the repo root

```bash
cd ~/Desktop/Ready_For_Robots
python3 -m alembic upgrade head
```

(Adjust `cd` to wherever you cloned the repo.)

Requires `gen_random_uuid()` (available on Supabase Postgres).

### Alternative: SQL only

If you prefer not to run Alembic locally, run the plain SQL file in the **Supabase SQL editor**: `migrations/sql/c7d8e9f0a1b2_add_crm_teams_core.sql`.

### Troubleshooting: `DuplicateTable: relation "companies" already exists`

That means Postgres **already has** tables from an earlier deploy or manual setup, but the **`alembic_version`** table is empty or behind—so Alembic tries to run the first migration again.

**If your database already matches everything through the “user tables” migration** (`user_profiles`, `user_saved_companies`, etc. exist), **stamp** that revision, then apply only what is left:

```bash
cd ~/Desktop/Ready_For_Robots
python3 -m alembic stamp a1b2c3d4e5f6
python3 -m alembic upgrade head
```

That tells Alembic “migrations through `a1b2c3d4e5f6` are already applied” and runs **`c7d8e9f0a1b2`** (CRM) only.

**Check in Supabase → SQL:**

```sql
SELECT * FROM alembic_version;
```

If the row is missing, stamping is appropriate. If you stamp too far ahead while tables are missing, later upgrades will fail—only stamp a revision that matches what is actually in the database.

**If you only need CRM tables** and already ran `migrations/sql/c7d8e9f0a1b2_add_crm_teams_core.sql` by hand, set Alembic to head without re-running:

```bash
python3 -m alembic stamp c7d8e9f0a1b2
```

## What was added

| Table | Role |
|-------|------|
| `teams` | Workspace boundary for CRM |
| `team_members` | `user_id` → `user_profiles.id`, `role` (e.g. owner/admin/member) |
| `crm_accounts` | SSOT for a **buyer** within a team; optional `company_id` → `companies.id` |
| `crm_engagements` | Separate deal/sales motion per account |
| `crm_tasks` | Tasks; optional `engagement_id`; `source` for agent/playbook/user |
| `crm_notes` | Notes on account or engagement |
| `agent_runs` | Audit trail for LLM plans (JSON in/out, tokens) |
| `crm_playbook_templates` | `team_id` null = global template; else team-scoped |

Partial unique index: at most one `crm_accounts` row per `(team_id, company_id)` when `company_id` is set.

## Optional: Supabase RLS

If the **browser** talks to Postgres via the Supabase client (not only FastAPI with service role), add row-level security. A sketch lives in `docs/crm_rls_sketch.sql`. FastAPI endpoints using the **service role** often bypass RLS; policies still matter for direct client access.

## Agent behavior

See `docs/agent-spec.md` for how `agent_runs` and tasks/notes interact.
