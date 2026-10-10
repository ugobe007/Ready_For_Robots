# Cal → Phelan Rename Migration Guide

**Date:** 2026-10-10  
**Breaking Change:** Yes - Requires configuration updates

---

## What Changed

Complete rename of "Cal" to "Phelan" throughout the codebase:
- 96 files modified
- 19 files renamed
- All function names, class names, variables updated
- Environment variables renamed
- Redis keys renamed
- Character persona name changed from "Cal" to "Phelan"

---

## Required Configuration Updates

### 1. Fly Secrets (CRITICAL - Do Before Deploying)

```bash
# Remove old secrets
fly secrets unset CAL_AUTONOMY_ENABLED -a ready-2-robot

# Set new secrets
fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot
```

### 2. All Environment Variables

| Old Name | New Name |
|----------|----------|
| `CAL_AUTONOMY_ENABLED` | `PHELAN_AUTONOMY_ENABLED` |
| `CAL_AUTONOMY_EVERY_HOURS` | `PHELAN_AUTONOMY_EVERY_HOURS` |
| `CAL_AUTONOMY_DAILY_CAP` | `PHELAN_AUTONOMY_DAILY_CAP` |
| `CAL_AUTONOMY_FIRST_RUN_DELAY_MINUTES` | `PHELAN_AUTONOMY_FIRST_RUN_DELAY_MINUTES` |
| `CAL_BUYER_SALES_ENABLED` | `PHELAN_BUYER_SALES_ENABLED` |
| `CAL_REVIEW_EMAIL` | `PHELAN_REVIEW_EMAIL` |
| `CAL_COMM_LEARNING_ENABLED` | `PHELAN_COMM_LEARNING_ENABLED` |
| `ENABLE_SCHEDULED_CAL_AUTONOMY` | `ENABLE_SCHEDULED_PHELAN_AUTONOMY` |
| `ENABLE_SCHEDULED_CAL_COMM_LEARNING` | `ENABLE_SCHEDULED_PHELAN_COMM_LEARNING` |

### 3. Redis Keys (Automatic Migration)

Redis keys will automatically use new names:
- `cal:autonomy:*` → `phelan:autonomy:*`
- `cal:outreach:*` → `phelan:outreach:*`
- `cal:comm_learning:*` → `phelan:comm_learning:*`
- `cal:bounce_pause:*` → `phelan:bounce_pause:*`

Old keys will expire naturally or can be manually cleaned up.

---

## Files Renamed

### Core Services
```
app/services/cal_autonomy.py → phelan_autonomy.py
app/services/cal_assembly_agent.py → phelan_assembly_agent.py
app/services/cal_daily_digest.py → phelan_daily_digest.py
app/services/cal_delivery_reconcile.py → phelan_delivery_reconcile.py
app/services/cal_draft_guard.py → phelan_draft_guard.py
app/services/cal_email_demo.py → phelan_email_demo.py
app/services/cal_email_send.py → phelan_email_send.py
app/services/cal_insights.py → phelan_insights.py
app/services/cal_lead_drops.py → phelan_lead_drops.py
app/services/cal_ops_monitor.py → phelan_ops_monitor.py
app/services/cal_outreach_send.py → phelan_outreach_send.py
app/services/cal_persona.py → phelan_persona.py
app/services/cal_pipeline_enrichment.py → phelan_pipeline_enrichment.py
app/services/cal_seller_brief.py → phelan_seller_brief.py
app/services/cal_voice_rubric.py → phelan_voice_rubric.py
app/services/cal_watchdog.py → phelan_watchdog.py
app/services/communication_learning_report.py → phelan_learning_report.py
```

### Scripts
```
scripts/cal_live_cycle_monitor.py → phelan_live_cycle_monitor.py
scripts/cal_dryrun.py → phelan_dryrun.py
```

---

## API Changes

### Function Names
- `cal_autonomy_enabled()` → `phelan_autonomy_enabled()`
- `run_cal_autonomy_cycle()` → `run_phelan_autonomy_cycle()`
- `get_cal_review_email()` → `get_phelan_review_email()`
- `record_cal_heartbeat()` → `record_phelan_heartbeat()`
- `communication_learning_enabled()` → `phelan_learning_enabled()`
- `send_communication_learning_report()` → `send_phelan_learning_report()`

### Import Changes
```python
# Old
from app.services.cal_autonomy import cal_autonomy_enabled
from app.services.communication_learning_report import send_communication_learning_report

# New
from app.services.phelan_autonomy import phelan_autonomy_enabled
from app.services.phelan_learning_report import send_phelan_learning_report
```

---

## Character/Persona Changes

The autonomous agent character is now "Phelan" instead of "Cal":

**Old messages:**
```
"Hi, I am Cal. I work at ReadyForRobots..."
"This is Cal from Ready For Robots..."
```

**New messages:**
```
"Hi, I am Phelan. I work at ReadyForRobots..."
"This is Phelan from Ready For Robots..."
```

---

## Deployment Steps

### Pre-Deployment Checklist

1. ✅ Review all changed files
2. ✅ Run tests: `pytest`
3. ✅ Check TypeScript compilation (if frontend changes)
4. ⚠️ **Update Fly secrets** (MUST DO BEFORE DEPLOY)

### Deployment Sequence

```bash
# Step 1: Update Fly secrets (do this FIRST)
fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot
fly secrets unset CAL_AUTONOMY_ENABLED -a ready-2-robot

# Step 2: Commit changes
git add -A
git commit -m "feat: rename Cal to Phelan throughout codebase

BREAKING CHANGE: All Cal-related environment variables, functions,
and modules renamed to Phelan. See CAL_TO_PHELAN_MIGRATION.md for
complete migration guide."

# Step 3: Push to branch
git push origin rename/cal-to-phelan

# Step 4: Create PR and review

# Step 5: After merge, deploy
fly deploy -a ready-2-robot --wait-timeout 600

# Step 6: Verify in logs
fly logs -a ready-2-robot | grep phelan-autonomy
```

---

## Verification

### Check Worker Started
```bash
fly logs -a ready-2-robot | grep "\[phelan-autonomy\]"
```

Should see:
```
[phelan-autonomy] scheduler thread started
```

### Check First Cycle
```bash
fly logs -a ready-2-robot | grep "Phelan autonomy cycle"
```

Should see (after ~20 min):
```
Phelan autonomy cycle: status=ok drafted=N sent=N
```

### Check Database
```bash
fly ssh console -a ready-2-robot
python3 -c "
from app.database import SessionLocal
from app.models.outreach import OutreachMessage
from datetime import datetime, timezone, timedelta

db = SessionLocal()
since = datetime.now(timezone.utc) - timedelta(hours=24)
count = db.query(OutreachMessage).filter(
    OutreachMessage.sent_at >= since,
    OutreachMessage.send_identity == 'phelan'
).count()
print(f'Phelan sends last 24h: {count}')
"
```

---

## Rollback Plan

If issues arise:

1. **Revert Fly secrets:**
```bash
fly secrets set CAL_AUTONOMY_ENABLED=1 -a ready-2-robot
fly secrets unset PHELAN_AUTONOMY_ENABLED -a ready-2-robot
```

2. **Rollback code:**
```bash
git revert <commit-sha>
git push origin main
fly deploy -a ready-2-robot
```

---

## Testing Checklist

- [ ] Python imports work
- [ ] Main.py worker startup succeeds
- [ ] Phelan autonomy thread starts
- [ ] First cycle runs without errors
- [ ] Emails send successfully
- [ ] Redis keys are created properly
- [ ] Admin panel shows Phelan (not Cal)
- [ ] Learning reports generate
- [ ] Persona name is "Phelan" in sent emails

---

## Impact Assessment

### What Breaks
- ❌ Old environment variables stop working
- ❌ Scripts/cron jobs using old names fail
- ❌ External monitoring expecting "cal" in logs

### What Continues Working
- ✅ Database (OutreachMessage table unchanged)
- ✅ Existing drafted messages (not resent)
- ✅ Reply classification
- ✅ CRM accounts
- ✅ All other services

---

## Timeline

| Time | Action |
|------|--------|
| T-10min | Update Fly secrets |
| T+0 | Deploy new code |
| T+20min | First Phelan cycle runs |
| T+6h | Second cycle, more sends |
| T+7d | First Phelan learning report |

---

## Support

If issues arise:
1. Check Fly logs: `fly logs -a ready-2-robot`
2. Check environment: `fly ssh console -a ready-2-robot` → `printenv | grep PHELAN`
3. Check this migration guide
4. Verify all secrets are updated

---

## Files Modified Summary

- **Services:** 16 files renamed, all imports updated
- **Scripts:** 20+ admin scripts updated
- **Tests:** 15+ test files updated
- **API:** All API endpoints updated
- **Main:** Worker startup logic updated
- **Docs:** Mission briefs and guides updated

**Total:** 96 files modified, 19 files renamed

---

## Success Criteria

✅ Deployment completes without errors  
✅ Phelan autonomy thread starts  
✅ First cycle runs and sends emails  
✅ No "Cal" references in logs  
✅ Learning report generates with "Phelan" branding  
✅ Admin panel reflects new naming  
✅ No import errors or broken dependencies
