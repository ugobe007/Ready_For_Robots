# Proposals, sender settings, and CRM outreach (FastAPI + Postgres + Next.js)

Canonical implementation in this repo. Use this document instead of copy-pasting from external prototypes.

## Stack

| Layer | Location |
|--------|----------|
| API | FastAPI under `app/api/` |
| Auth | `Authorization: Bearer <Supabase access_token>` → `Depends(_require_user)` in `app/api/auth_deps.py` |
| DB | Postgres (`DATABASE_URL`, typically Supabase). SQLAlchemy `get_db` in `app/database.py` |
| Migrations | Alembic: `migrations/versions/*.py` — chain from current `alembic heads` |

## API routes (no double prefixes)

`app/main.py` mounts routers with a prefix. Handlers use **relative** paths only.

| Method | Full URL | Handler module |
|--------|-----------|----------------|
| `POST` | `/api/proposals` | `app/api/proposals.py` — upsert saved proposal (unique per user + company name) |
| `GET` | `/api/proposals` | List current user’s proposals |
| `GET` | `/api/proposals/{id}` | Get one by UUID |
| `DELETE` | `/api/proposals/{id}` | Delete one |
| `POST` | `/api/proposals/pdf` | Generate PDF (auth required); footer uses `user_settings` |
| `GET` | `/api/user/settings` | `app/api/user.py` — proposal sender fields |
| `PUT` | `/api/user/settings` | Upsert `user_settings` |
| `PATCH` | `/api/crm/accounts/{account_id}` | Update `contact_email`, `outreach_draft` (team-scoped); optional partial body |
| `POST` | `/api/crm/accounts/{account_id}/send-outreach` | Resend email + set `outreach_stage` to `intro_sent` on success |

Outreach is always keyed by **CRM account UUID**, not by `/api/leads/{id}`.

## Tables

- **`pipeline_proposals`**: `id`, `user_id` (FK `user_profiles.id`), optional `company_id` (FK `companies.id`), `company_name`, `proposal_text`, optional `contact_email`, timestamps. **UNIQUE (`user_id`, `company_name`)** for upsert.
- **`user_settings`**: PK `user_id`; `sender_name`, `sender_title`, `sender_company`, `sender_email`, `updated_at`.
- **`crm_accounts`** (added columns): `contact_email`, `outreach_draft`, `outreach_sent_at`, `outreach_stage`.

## Resend

Reuse `app/services/resend_email.py` (`send_email_via_resend`). Env: `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, optional `RESEND_REPLY_TO`. Optional display name is passed for the `From` header when present.

## Frontend

- **`frontend/nextjs/lib/apiBase.js`**: `getApiBase()` for API origin.
- **`frontend/nextjs/pages/profile.js`**: Proposal sender settings → `GET`/`PUT` `/api/user/settings` (paths are appended to `getApiBase()` like other `/api/user/*` calls).
- **`frontend/nextjs/pages/crm.js`**: Outreach editor, `PATCH` account, `POST` send-outreach, `POST` proposal PDF with Bearer token.

## Deploy order

1. Land migrations; run `alembic upgrade head` against the same database as production `DATABASE_URL`.
2. Deploy FastAPI (Fly). Ensure `RESEND_API_KEY` and `RESEND_FROM_EMAIL` are set before using send-outreach.
3. Deploy Next.js (Vercel) so CRM/profile pick up new UI.

## Production wiring (Vercel + Fly)

1. **Vercel environment variables** (Production + Preview as needed), matching `frontend/nextjs/.env.example`:
   - `NEXT_PUBLIC_API_URL` = your FastAPI origin, e.g. `https://ready-2-robot.fly.dev` (never the static site URL).
   - `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (or publishable key) from [Supabase Dashboard](https://supabase.com/dashboard) → Project → Settings → API.
2. **Fly `CORS_ORIGINS`** must include every browser origin that calls the API (comma-separated, no spaces). The repo’s `fly.toml` `[env]` includes marketing domains, Fly, local dev, and **`https://ready-for-robots-ax5i.vercel.app`**. Add custom domains or extra Vercel preview URLs the same way. `app/main.py` defaults include the same Vercel host when `CORS_ORIGINS` is unset.
3. **JWT**: Fly must have `SUPABASE_JWT_SECRET` (or `SUPABASE_URL` for JWKS) so `Authorization: Bearer` from the Next app is accepted.
4. **Meta override**: In production, `_app.js` emits `<meta name="rfr-api-base" content="…">` from `NEXT_PUBLIC_API_URL` at build time so `getApiBase()` can recover even if an old bundle had a wrong API URL.
