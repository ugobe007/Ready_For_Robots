# Scripts & commands cheat sheet

Run everything from the **repo root**:

`/Users/robertchristopher/Desktop/Ready_For_Robots`

Ensure **`DATABASE_URL`** is set (usually via `.env` and/or `frontend/nextjs/.env.local`). Python scripts load both.

---

## 1. Database migrations (Alembic)

Apply schema changes (e.g. new columns):

```bash
python3 -m alembic upgrade head
```

Offline SQL for `automation_profile` only (optional; Alembic normally handles it):

```bash
# Run in Supabase SQL editor if needed
cat scripts/sql/add_company_automation_profile_column.sql
```

---

## 2. Lead cleanup pipeline (recommended)

**Dry run** (no writes):

```bash
python3 scripts/cleanup_leads.py
```

**Apply — safe default (purge junk + headline renames + rebuild profiles; industry only fills empty / Unknown / Other / New):**

```bash
python3 scripts/cleanup_leads.py --apply
```

**Apply — skip industry entirely** (if you only want purge + names + profiles):

```bash
python3 scripts/cleanup_leads.py --apply --skip-industry
```

**Apply — skip purge** (only names / industry / profiles):

```bash
python3 scripts/cleanup_leads.py --apply --skip-purge
```

**Dangerous — overwrite every company’s industry from keywords** (only if you intend to):

```bash
python3 scripts/cleanup_leads.py --apply --force-industry
```

**Other flags:**

```bash
python3 scripts/cleanup_leads.py --apply --skip-names
python3 scripts/cleanup_leads.py --apply --skip-profiles
python3 scripts/cleanup_leads.py --apply --limit-names 200
```

---

## 3. Purge junk names only (legacy)

Preview junk rows:

```bash
python3 scripts/purge_junk_leads.py
```

Delete junk:

```bash
python3 scripts/purge_junk_leads.py --delete
python3 scripts/purge_junk_leads.py --delete --limit 500
```

*(Prefer `cleanup_leads.py` for a full pipeline.)*

---

## 4. Industry: unknown rows only

Fills industry for companies still marked Unknown (does not blast every row):

```bash
python3 scripts/reclassify_unknown_industries.py
```

---

## 5. Scores

Recalculate scores (when you have such a workflow wired):

```bash
python3 scripts/recalculate_all_scores.py
```

---

## 6. Frontend (Next.js static export)

```bash
cd frontend/nextjs
npm ci
npm run build
```

Local dev (API on `:8000`):

```bash
npm run dev
```

---

## 7. Backend + worker locally

Docker/Fly image uses:

```bash
bash scripts/start_all.sh
```

*(Starts Celery beat/worker + uvicorn; used in production image.)*

---

## 8. Deploy (Fly.io)

From repo root:

```bash
fly deploy
```

---

## 9. Tests

```bash
python3 -m pytest tests/ -q
```

Focused:

```bash
python3 -m pytest tests/test_automation_profile.py tests/test_industry_inference.py tests/test_company_name_inference.py tests/test_lead_filter_junk.py -q
```

---

## 10. Admin API (junk purge via HTTP)

If `ADMIN_KEY` is set on the server (use the **secret value** you chose when running
`fly secrets set ADMIN_KEY=...` — **not** the 16-char hex digest shown by `fly secrets list`):

```bash
curl -sS -X POST "https://ready-2-robot.fly.dev/api/admin/purge-junk" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-actual-admin-key-string" \
  -d '{"dry_run": true}'
```

Set `"dry_run": false` to delete (same logic as `is_junk`).

**Lead inference / enrichment agent** (same `X-Admin-Key`, or admin Supabase JWT):

```bash
curl -sS -X POST "https://ready-2-robot.fly.dev/api/admin/leads/enrich-agent?limit=300" \
  -H "X-Admin-Key: YOUR_ADMIN_KEY"
```

Do **not** use the literal string `YOUR_ADMIN_JWT` — that is documentation placeholder only. For JWT auth, sign in on the site as an `ADMIN_EMAILS` user and copy the real `access_token` from the browser (DevTools → Application → localStorage, key containing `auth-token`).

---

## 11. Optional / data ops (use when you know you need them)

| Script | Purpose |
|--------|--------|
| `scripts/check_db_connection.py` | Verify DB connectivity |
| `scripts/check_supabase.py` | Supabase checks |
| `scripts/seed_leads_v2.py` / `seed_leads_v3.py` | Large seed (destructive / dev) |
| `scripts/quick_seed.py` | Small seed |
| `scripts/run_intelligence_scraper.py` | In-process intelligence scrape |
| `scripts/watch_leads.py` | TUI watch |
| `scripts/audit_pipeline.py` | Pipeline audit |
| `scripts/sync_from_production.py` | Sync (read script before use) |
| `scripts/merge_duplicate_companies_by_domain.py` | Merge duplicate `companies` rows that share `website_domain` (dry-run default; `--execute` to apply). Requires `website_domain` column (Alembic). |

---

## Quick “happy path” after pulling main

```bash
cd /Users/robertchristopher/Desktop/Ready_For_Robots
python3 -m alembic upgrade head
python3 scripts/cleanup_leads.py
python3 scripts/cleanup_leads.py --apply --skip-industry   # or --apply for conservative industry fill
cd frontend/nextjs && npm ci && npm run build && cd ../..
fly deploy   # when ready
```
