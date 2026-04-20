# Scripts

Run from the **repository root** (the directory that contains `app/` and `scripts/`). Each script’s flags are in its file docstring at the top.

If you use a **git worktree**, that root is a separate folder from another clone on disk; your `.env` may only exist in one clone. Point Python at it with `DOTENV_PATH` (see `cleanup_leads.py` header) or copy `.env` into the worktree root.

Database URL loading matches `app/database.py` (repo `.env`, `frontend/nextjs/.env.local`, optional `DOTENV_PATH`).

---

## Bash commands (copy-paste)

Use a shell where the venv is activated if your project uses one (`source venv/bin/activate`). Adjust `cd` and `DOTENV_PATH` to match your machine.

**Go to the repo root and optionally point at the `.env` that has `DATABASE_URL`:**

```bash
cd /path/to/repository-root
export DOTENV_PATH=/path/to/.env
```

---

### Check database

```bash
python3 scripts/check_db_connection.py
```

---

### Scrape / intelligence pipeline (news discovery)

```bash
python3 scripts/run_intelligence_scraper.py
```

```bash
python3 scripts/run_intelligence_scraper.py --mode discover --limit 10
```

(`--mode` can be `discover`, `enrich`, or `both` — see the script’s docstring.)

---

### API only (local dev)

```bash
bash scripts/run_local.sh
```

---

### API + migrations + Celery worker and beat

Requires broker/Redis env vars to be set (see deploy config). From repo root:

```bash
bash scripts/start_all.sh
```

---

### Queue all scraper tasks via Celery

Use only when a Celery worker is already running and pointed at the same broker/DB.

```bash
celery -A worker.celery_worker call worker.tasks.run_all_scrapers_task
```

---

### Lead cleanup and automation profiles

Dry run (prints plan, no writes):

```bash
python3 scripts/cleanup_leads.py --skip-industry
```

Apply (deletes invalid names per `is_valid_lead`, normalizes, optional steps, rebuilds profiles):

```bash
python3 scripts/cleanup_leads.py --apply --skip-industry
```

---

### Quality export and industry audit

```bash
python3 scripts/export_quality_decision_log.py -o data/quality_log.jsonl
```

```bash
python3 scripts/examine_industry_mismatch.py --sample 50
```

```bash
python3 -m pytest tests/test_quality_decision_log.py -q
```

---

## Lead quality: which “gate” does each script use?

Production ingest and the admin API use **`company_validator.is_valid_lead`** (plus `text_classifier` when applicable).  
Some utilities only call **`lead_filter.is_junk`** — faster, but **stricter/narrower** than full validation. Results will not match `is_valid_lead` 1:1.

| Gate | Scripts |
|------|---------|
| **`is_valid_lead` (matches ingest purge behavior)** | `cleanup_leads.py` — deletes rows that fail the full gate |
| **`is_junk` only** | `audit_junk_names.py`, `purge_junk_leads.py` — audit/delete using the fast junk filter only |
| **Mixed / reporting** | `scan_headline_fragment_names.py` — patterns + `is_junk` for labeling |
| **Full stack export (junk + classifier + `is_valid_lead`)** | `export_quality_decision_log.py` — JSONL for review / ML |
| **Industry audit (read-only)** | `examine_industry_mismatch.py` — rows where `infer_industry_from_text` ≠ stored and ≠ `Unknown` (same blob as `cleanup_leads`) |
| **Monitoring** | `watch_leads.py` — uses `classify_lead` / `is_junk` for live checks (see code for exact behavior) |

Seeds (`seed_leads_v2.py`, `seed_leads_v3.py`, `quick_seed.py`, …), dedup helpers, and recovery scripts are **operational**; they are not the specification for hot-path validation. Check each file’s docstring before relying on it.

## Canonical documentation

- **[docs/lead_quality_north_star.md](../docs/lead_quality_north_star.md)** — goals and ingest contract  
- **[docs/lead_quality_pipeline.md](../docs/lead_quality_pipeline.md)** — stage order and commands  
- **[docs/lead_quality_blind_spots.md](../docs/lead_quality_blind_spots.md)** — how defenses stack  

## Quick reference (same commands, one block)

```bash
python3 scripts/check_db_connection.py
python3 scripts/run_intelligence_scraper.py
bash scripts/run_local.sh
python3 scripts/cleanup_leads.py --apply --skip-industry
python3 scripts/export_quality_decision_log.py -o data/quality_log.jsonl
python3 scripts/examine_industry_mismatch.py --sample 30
python3 scripts/audit_junk_names.py --limit 200
python3 -m pytest tests/test_quality_decision_log.py -q
```
