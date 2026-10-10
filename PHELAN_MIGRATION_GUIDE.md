# Cal → Phelan Migration Guide

**Date**: Saturday, October 10, 2026  
**Branch**: `rename/phelan-identifiers-67bd`  
**Base**: Current `main` (commit `ba509d26`)

## What Changed

Complete rename of Cal autonomous outreach system to Phelan:
- **55 files renamed** (`cal_*.py` → `phelan_*.py`)
- **140+ files updated** with identifier replacements
- **Phelan voice content preserved** (already updated on main)

## Files Renamed

### Services (17 files)
```
cal_assembly_agent.py       → phelan_assembly_agent.py
cal_autonomy.py              → phelan_autonomy.py
cal_daily_digest.py          → phelan_daily_digest.py
cal_delivery_reconcile.py    → phelan_delivery_reconcile.py
cal_draft_guard.py           → phelan_draft_guard.py
cal_email_demo.py            → phelan_email_demo.py
cal_email_send.py            → phelan_email_send.py
cal_insights.py              → phelan_insights.py
cal_jobs_desk.py             → phelan_jobs_desk.py
cal_lead_drops.py            → phelan_lead_drops.py
cal_ops_monitor.py           → phelan_ops_monitor.py
cal_outreach_send.py         → phelan_outreach_send.py
cal_persona.py               → phelan_persona.py
cal_pipeline_enrichment.py   → phelan_pipeline_enrichment.py
cal_seller_brief.py          → phelan_seller_brief.py
cal_voice_rubric.py          → phelan_voice_rubric.py
cal_watchdog.py              → phelan_watchdog.py
communication_learning_report.py → phelan_learning_report.py
```

### Tests (18 files)
```
test_cal_assembly_agent.py       → test_phelan_assembly_agent.py
test_cal_autonomy.py              → test_phelan_autonomy.py
test_cal_autonomy_toggle.py       → test_phelan_autonomy_toggle.py
test_cal_daily_digest.py          → test_phelan_daily_digest.py
test_cal_draft_guard.py           → test_phelan_draft_guard.py
test_cal_email_demo.py            → test_phelan_email_demo.py
test_cal_hermes_priority.py       → test_phelan_hermes_priority.py
test_cal_insights.py              → test_phelan_insights.py
test_cal_jobs_desk.py             → test_phelan_jobs_desk.py
test_cal_jobs_digest_gates.py     → test_phelan_jobs_digest_gates.py
test_cal_lead_drops.py            → test_phelan_lead_drops.py
test_cal_ops_and_conversion.py    → test_phelan_ops_and_conversion.py
test_cal_outreach_send.py         → test_phelan_outreach_send.py
test_cal_safe_rotate.py           → test_phelan_safe_rotate.py
test_cal_seller_brief.py          → test_phelan_seller_brief.py
test_cal_voice.py                 → test_phelan_voice.py
test_cal_voice_rubric.py          → test_phelan_voice_rubric.py
test_cal_watchdog.py              → test_phelan_watchdog.py
```

### Scripts (20 files)
```
cal_block_suppressed_enrollments.py → phelan_block_suppressed_enrollments.py
cal_bounce_recovery.py              → phelan_bounce_recovery.py
cal_contact_audit.py                → phelan_contact_audit.py
cal_contact_live_sample.py          → phelan_contact_live_sample.py
cal_dryrun.py                       → phelan_dryrun.py
cal_hunter_reenrich.py              → phelan_hunter_reenrich.py
cal_ineligible_breakdown.py         → phelan_ineligible_breakdown.py
cal_intro_blockers.py               → phelan_intro_blockers.py
cal_live_cycle_monitor.py           → phelan_live_cycle_monitor.py
cal_log_learning.py                 → phelan_log_learning.py
cal_pipeline_report.py              → phelan_pipeline_report.py
cal_pool_contamination.py           → phelan_pool_contamination.py
cal_preflight.py                    → phelan_preflight.py
cal_proof_batch_send.py             → phelan_proof_batch_send.py
cal_quarantine_dead_domain_contacts.py → phelan_quarantine_dead_domain_contacts.py
cal_recent_sends.py                 → phelan_recent_sends.py
cal_runway.py                       → phelan_runway.py
cal_score_draft.py                  → phelan_score_draft.py
cal_send_curated.py                 → phelan_send_curated.py
```

## Environment Variables Migration

### REQUIRED - Update on Fly Before Deploy

```bash
# Primary autonomy toggle
fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot
fly secrets unset CAL_AUTONOMY_ENABLED -a ready-2-robot

# Optional: Keep legacy name as alias during transition
# (code checks PHELAN_* first, falls back to CAL_*)
# fly secrets set ENABLE_SCHEDULED_PHELAN_AUTONOMY=1 -a ready-2-robot
```

### Full Environment Variable Mapping

| Old (Cal) | New (Phelan) | Purpose |
|-----------|--------------|---------|
| `CAL_AUTONOMY_ENABLED` | `PHELAN_AUTONOMY_ENABLED` | Enable autonomous worker loop |
| `ENABLE_SCHEDULED_CAL_AUTONOMY` | `ENABLE_SCHEDULED_PHELAN_AUTONOMY` | Legacy toggle (fallback) |
| `CAL_AUTONOMY_EVERY_HOURS` | `PHELAN_AUTONOMY_EVERY_HOURS` | Cycle interval (default: 6) |
| `CAL_AUTONOMY_DAILY_CAP` | `PHELAN_AUTONOMY_DAILY_CAP` | Max sends per day |
| `CAL_AUTONOMY_FIRST_RUN_DELAY_MINUTES` | `PHELAN_AUTONOMY_FIRST_RUN_DELAY_MINUTES` | Startup delay (default: 20) |
| `CAL_BUYER_SALES_ENABLED` | `PHELAN_BUYER_SALES_ENABLED` | Robot-sales intros to buyers |
| `CAL_REVIEW_EMAIL` | `PHELAN_REVIEW_EMAIL` | Operator inbox for format reviews |
| `CAL_ADMIN_USER_ID` | `PHELAN_ADMIN_USER_ID` | Admin context for outreach |
| `CAL_BOUNCE_ALERT_COOLDOWN_HOURS` | `PHELAN_BOUNCE_ALERT_COOLDOWN_HOURS` | Bounce alert cooldown (default: 12) |
| `CAL_VARIANT_MIN_SENDS` | `PHELAN_VARIANT_MIN_SENDS` | Min sends before judging variant (default: 12) |
| `CAL_VARIANT_MAX_NEG_RATE` | `PHELAN_VARIANT_MAX_NEG_RATE` | Max negative rate (default: 0.40) |
| `CAL_INCLUDE_SIGNAL_REASON` | `PHELAN_INCLUDE_SIGNAL_REASON` | Include signal reasoning in copy |

## Code Changes

### Python Imports
```python
# Old
from app.services.cal_autonomy import cal_autonomy_enabled, run_cal_autonomy_cycle
from app.services.cal_persona import cal_signature

# New
from app.services.phelan_autonomy import phelan_autonomy_enabled, run_phelan_autonomy_cycle
from app.services.phelan_persona import phelan_signature
```

### Function Names
```python
# Old
cal_autonomy_enabled()
run_cal_autonomy_cycle(db)
cal_opening(audience="buyer")
cal_vendor_opening(reminder=False)

# New
phelan_autonomy_enabled()
run_phelan_autonomy_cycle(db)
phelan_opening(audience="buyer")
phelan_vendor_opening(reminder=False)
```

### Constants
```python
# Old
CAL_INTRO
CAL_BUYER_ROLE_LINE
CAL_VENDOR_IDENTITY
CAL_BANNED_PHRASES

# New
PHELAN_INTRO
PHELAN_BUYER_ROLE_LINE
PHELAN_VENDOR_IDENTITY
PHELAN_BANNED_PHRASES
```

### Redis Keys
```python
# Old
"cal:outreach:template_fingerprint"
"cal:autonomy:runtime_enabled"

# New
"phelan:outreach:template_fingerprint"
"phelan:autonomy:runtime_enabled"
```

### Thread/Daemon Names
```python
# Old
threading.Thread(..., name="cal-autonomy")
print("[cal-autonomy] scheduler thread started")

# New
threading.Thread(..., name="phelan-autonomy")
print("[phelan-autonomy] scheduler thread started")
```

## Database Tables

**No changes required** - tables use generic names:
- `outreach_messages` (not `cal_outreach_messages`)
- `outreach_replies` (not `cal_outreach_replies`)

## What Was NOT Changed

### Content Preserved
The Phelan voice content (messaging, tone, persona) that was already updated on main is **preserved exactly as-is**:

```python
PHELAN_INTRO = (
    "I'm Phelan, Robot Job Analyst at ReadyForRobots. ReadyForRobots is recruitment and placement infrastructure for robotic labor. "
    "We evaluate physical task feasibility, cell constraints, payload/throughput requirements, and hardware capabilities "
    "to match qualified robotic labor directly to real, verified job openings at enterprise and industrial facilities."
)
```

This rename only changes **identifiers** (variable names, function names, file names), not the **content** of what Phelan says.

### Database Tables
Table names remain generic (`outreach_messages`, not `cal_outreach_messages`).

### API Endpoints
No public API endpoint changes.

## Deployment Steps

### 1. Pre-Deploy Verification (Local)

```bash
# Run tests on rename branch
cd /workspace
git checkout rename/phelan-identifiers-67bd

# Check imports
python3 -c "from app.services.phelan_autonomy import phelan_autonomy_enabled; print('✓ imports work')"

# Run test suite
pytest tests/test_phelan_*.py -v
```

### 2. Update Fly Secrets

```bash
# Set new Phelan variables
fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot
fly secrets set RESEND_API_KEY=<your_key> -a ready-2-robot

# Unset old Cal variables (optional, but clean)
fly secrets unset CAL_AUTONOMY_ENABLED -a ready-2-robot
```

### 3. Deploy

```bash
# Merge PR to main
# GitHub Actions will deploy automatically
# Or manually:
git checkout main
git merge rename/phelan-identifiers-67bd
git push origin main
fly deploy -a ready-2-robot --wait-timeout 600
```

### 4. Post-Deploy Verification

```bash
# Check worker started
fly logs -a ready-2-robot | grep -i "phelan-autonomy"

# Should see:
# [phelan-autonomy] scheduler thread started
# Phelan autonomy thread started (every 6 hours)
```

### 5. Monitor First Cycle

```bash
# Wait 20-40 minutes for first cycle
fly logs -a ready-2-robot --lines 100 | grep -i "Phelan autonomy cycle"

# Should see:
# Phelan autonomy cycle: status=ok drafted=N sent=M format_notified=...
```

### 6. Verify Resend Dashboard

1. Log in to https://resend.com/emails
2. Check for recent sends
3. Verify variant tags are attached

## Rollback Plan

If issues occur after deploy:

```bash
# Option A: Revert secrets (keep code as-is)
fly secrets set CAL_AUTONOMY_ENABLED=0 -a ready-2-robot
fly secrets set PHELAN_AUTONOMY_ENABLED=0 -a ready-2-robot

# Option B: Revert code
git revert <merge-commit-sha>
git push origin main
fly deploy -a ready-2-robot --wait-timeout 600

# Option C: Emergency disable
fly ssh console -a ready-2-robot
# Inside container:
export PHELAN_AUTONOMY_ENABLED=0
pkill -f "ready_for_robots"  # Restart worker
```

## Testing Checklist

- [ ] All 55 file renames committed
- [ ] All imports updated (no `from app.services.cal_*`)
- [ ] All function calls updated (no `cal_*()` calls)
- [ ] All env vars updated in code (check `os.getenv("PHELAN_*")`)
- [ ] Redis keys updated (check `"phelan:*"`)
- [ ] Thread names updated (check `"phelan-autonomy"`)
- [ ] Test suite passes (`pytest tests/test_phelan_*.py`)
- [ ] Fly secrets configured (`PHELAN_AUTONOMY_ENABLED=1`)
- [ ] Worker loop starts on deploy
- [ ] First cycle completes successfully
- [ ] Resend dashboard shows sends
- [ ] No errors in Fly logs

## Notes

- **Phelan voice** (content/messaging) was already updated on main before this rename
- This PR only renames **identifiers** (variables, functions, files)
- **No database migrations** required
- **No API changes** for external consumers
- Worker loop behavior unchanged - still runs every 6 hours
- Learning report still runs weekly on Sundays

## Related Documentation

- `docs/phelan_persona_spec.md` - Phelan voice and persona guide
- `docs/phelan_learning_log.md` - Communication learning system
- `ENABLE_PHELAN_GUIDE.md` - How to enable Phelan autonomy
- `app/services/phelan_autonomy.py` - Core autonomy engine

## Success Metrics

After deploy, within 26 hours:
- ✅ Worker log shows `[phelan-autonomy] scheduler thread started`
- ✅ First cycle log shows `Phelan autonomy cycle: status=ok`
- ✅ Resend dashboard shows recent sends
- ✅ No import errors or crashes in Fly logs
- ✅ Next Sunday's learning report includes data

---

**Questions?** Check `app/services/phelan_autonomy.py` for runtime behavior or `docs/phelan_persona_spec.md` for voice guidelines.
