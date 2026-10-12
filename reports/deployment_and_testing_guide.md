# Deployment and Testing Guide - Human Labor Filtering

## Status

✅ **Code Changes**: All commits pushed to `main`  
⏳ **Deployment**: GitHub Actions will deploy automatically  
⏳ **Test Email**: Ready to send once deployment completes

---

## Commits Pushed

1. **`b65ae8b6`** - Ingest Grace Gong Physical AI Hiring List (Week 98)
2. **`cfaf9d32`** - Add supply/demand distinction verification and proper tagging
3. **`6a34b9c2`** - Enhance human labor filtering for top 25 robot jobs

---

## Automatic Deployment

The `.github/workflows/deploy.yml` workflow will:

1. ✓ Detect no migration changes (skip release command)
2. ✓ Deploy to Fly app: `ready-2-robot`
3. ✓ Wait for health check
4. ✓ Restart machines with new code

**Monitor deployment**: https://github.com/ugobe007/Ready_For_Robots/actions

---

## How to Send Test Email (After Deployment)

### Option 1: Via API with ADMIN_KEY (Recommended)

```bash
# Get ADMIN_KEY from Fly secrets
fly secrets list -a ready-2-robot | grep ADMIN_KEY

# Send test email
curl -X POST https://ready-2-robot.fly.dev/api/v1/market-graph/daily-jobs-report-send \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" \
  -d '{"force": true, "limit": 25}'
```

**Response (success):**
```json
{
  "sent": true,
  "date": "2026-10-12",
  "recipients": ["ugobe07@gmail.com"],
  "count": 25,
  "resend_id": "abc123...",
  "jobs": [...],
  "engine": "local_inference",
  "paid_llm": false
}
```

### Option 2: Via Fly SSH

```bash
# SSH into the Fly machine
fly ssh console -a ready-2-robot

# Run Python script
python3 << 'EOF'
from app.database import SessionLocal
from app.services.daily_jobs_report import send_daily_jobs_report

db = SessionLocal()
result = send_daily_jobs_report(db, force=True, limit=25)
print(f"Sent: {result.get('sent')}")
print(f"Recipients: {result.get('recipients')}")
print(f"Count: {result.get('count')}")
print(f"Resend ID: {result.get('resend_id')}")
db.close()
EOF
```

### Option 3: Via Admin Panel

1. Navigate to: https://readyforrobots.com/admin#daily-jobs-report
2. Log in with admin account
3. Click "Send Email Now" button

---

## What the Test Email Will Contain

### Email Details

- **To**: ugobe07@gmail.com (default recipient)
- **Subject**: "Top 25 hot job opportunities — 2026-10-12"
- **Attachment**: `daily-jobs-2026-10-12.csv`

### Email Content Format

```
Top 25 hot job opportunities — 2026-10-12

Each row is an employer asking for a robot.

01  Amazon Fulfillment Center · Seattle
    Job: Pick cases or eaches from storage
    Decision maker: Not named on the posting
    Contact: careers@amazon.com
    Robots: Piece-picking robot...

02  Marriott Hotels · Downtown District
    Job: Clean hard floors on a route
    Decision maker: Facilities Manager (Looked for: Director of Ops)
    Contact: https://marriott.com/careers/apply
    Robots: Floor scrubber...

...

CSV of these leads is attached (daily-jobs-2026-10-12.csv).
FIND: https://readyforrobots.com/?visit=jobs
Admin: https://readyforrobots.com/admin#daily-jobs-report
```

---

## Verifying Human Labor Filtering Worked

### What You Should See

✅ **Every job explicitly mentions robots**:
   - "AMR for warehouse"
   - "Autonomous floor scrubber"
   - "Hospital delivery robot"

✅ **No human hiring language**:
   - NOT "Warehouse Associate - $18/hr - Apply Now"
   - NOT "Housekeeper Needed - Full Time"
   - NOT "Robot Operator - Experience Required"

### Red Flags (Should NOT Appear)

If you see any of these patterns, the filtering failed:

❌ "Hiring", "Apply Now", "Resume Required"  
❌ "Full-time position", "Part-time role"  
❌ "Benefits package", "401k", "Health insurance"  
❌ "$XX/hr", "Salary range", "Competitive pay"  
❌ "Experience required", "Degree preferred"  
❌ "Background check", "Drug test", "Interview"

---

## Audit Current Top 25 (Once DATABASE_URL Available)

```bash
# Check for contamination
python3 scripts/audit_clean_top_25_jobs.py --dry-run

# Expected output if clean:
# ✓ CLEAN ROBOT JOBS: 25
# ✗ HUMAN LABOR CONTAMINATION: 0
# ✅ NO HUMAN LABOR CONTAMINATION FOUND

# If contamination found, clean it:
python3 scripts/audit_clean_top_25_jobs.py --apply
```

---

## Monitoring

### Check Deployment Status

```bash
# View recent deployments
fly status -a ready-2-robot

# Check logs
fly logs -a ready-2-robot --max 100

# Verify health
curl -sS https://ready-2-robot.fly.dev/api/v1/health
```

### Verify Enhanced Filters Are Live

```bash
# Check that the enhanced regex is deployed
fly ssh console -a ready-2-robot
python3 -c "
from app.services.robot_job_extract import _PERSON_HIRE_RE
import re
# Should include new patterns like 'hiring', 'full-time', 'benefits'
pattern = _PERSON_HIRE_RE.pattern
print('Enhanced filter includes hiring:', 'hiring' in pattern)
print('Enhanced filter includes full-time:', 'full-time' in pattern.replace('-', '_'))
print('Enhanced filter includes benefits:', 'benefits' in pattern)
"
```

---

## Troubleshooting

### Issue: Email Not Sent

**Check 1**: Is RESEND_API_KEY configured?
```bash
fly secrets list -a ready-2-robot | grep RESEND_API_KEY
```

**Check 2**: Check logs for errors
```bash
fly logs -a ready-2-robot | grep -i "daily jobs report"
```

**Check 3**: Try force send
```bash
# Force bypasses "already sent today" check
curl -X POST https://ready-2-robot.fly.dev/api/v1/market-graph/daily-jobs-report-send \
  -H "X-Admin-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"force": true, "limit": 25}'
```

### Issue: Human Labor Still in Top 25

**Step 1**: Run audit
```bash
python3 scripts/audit_clean_top_25_jobs.py --dry-run
```

**Step 2**: If contamination found, clean it
```bash
python3 scripts/audit_clean_top_25_jobs.py --apply
```

**Step 3**: Verify enhanced filters are deployed
```bash
# Check _PERSON_HIRE_RE includes new patterns
```

### Issue: Deployment Failed

**Check GitHub Actions**:
- Visit: https://github.com/ugobe007/Ready_For_Robots/actions
- Look for "Deploy to Fly.io" workflow
- Check logs for errors

**Manual deploy (if needed)**:
```bash
fly deploy -a ready-2-robot --wait-timeout 600
```

---

## Success Criteria

✅ Deployment completed successfully  
✅ Test email sent to ugobe07@gmail.com  
✅ All 25 jobs explicitly ask for robots  
✅ No human hiring language in any job  
✅ CSV attachment included  
✅ Jobs have employer names and robot descriptions

---

## Next Steps After Testing

1. **Verify email content** - Check ugobe07@gmail.com inbox
2. **Review CSV** - Open attachment, verify all jobs are robot requests
3. **Run audit** - Use `audit_clean_top_25_jobs.py` to verify cleanliness
4. **Add to weekly checklist** - Run audit every Monday before daily report
5. **Monitor contamination rate** - Track over time (target: 0%)

---

## Related Files

- **Deployment workflow**: `.github/workflows/deploy.yml`
- **Daily jobs service**: `app/services/daily_jobs_report.py`
- **Filter logic**: `app/services/robot_job_extract.py`
- **Audit tool**: `scripts/audit_clean_top_25_jobs.py`
- **Documentation**: `docs/human_labor_filtering.md`

---

**Summary**: Code is pushed and will deploy automatically via GitHub Actions. Once deployed, send a test email using the API endpoint with X-Admin-Key header to verify the enhanced human labor filtering is working.
