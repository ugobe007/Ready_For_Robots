# Enable Cal Autonomy & Phelan Learning - Setup Guide

**Current Status:**
- ✅ `RESEND_API_KEY` is set
- ❌ `PHELAN_AUTONOMY_ENABLED` not set
- ❌ `ENABLE_SCHEDULED_PHELAN_AUTONOMY` not set

---

## Quick Fix: Enable Cal Autonomy

### Option 1: Environment Variable (Recommended)
Set on your Fly app:

```bash
fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot
```

### Option 2: Runtime Toggle via Admin Panel
Visit https://readyforrobots.com/admin and look for the Cal autopilot toggle. This sets a Redis flag that overrides the env var.

---

## How It Works

### 1. Scheduled Worker Thread
The worker process runs `_scheduled_cal_autonomy_loop()` every 6 hours (configurable via `PHELAN_AUTONOMY_EVERY_HOURS`).

**Start conditions:**
- Must be running on **worker process** (not web)
- Either:
  - `ENABLE_SCHEDULED_PHELAN_AUTONOMY=1` (defaults to 1), OR
  - Running on Fly (has `FLY_APP_NAME`)

### 2. Autonomy Enabled Check
Each cycle checks `phelan_autonomy_enabled()`:
1. If `PHELAN_AUTONOMY_ENABLED=0` → disabled (hard override)
2. Else check Redis runtime toggle
3. Else check `ENABLE_SCHEDULED_PHELAN_AUTONOMY` env var

**If disabled:** Thread sleeps 1 hour and checks again

### 3. When Enabled
Every cycle (default 6h):
1. Drafts intro emails for hot leads
2. Tags each with a trust-first angle (variant_id)
3. Sends via Resend (respects daily cap, default 10/day)
4. Sends follow-ups to engaged threads
5. Records heartbeat to Redis

### 4. Phelan Learning
Once sends start:
- `OutreachMessage` records have `payload.variant_id` (angle tag)
- Replies classified by `reply_classifier.py`
- Weekly report aggregates performance by angle
- Sent to `ADMIN_EMAIL` every 7 days

---

## Configuration Reference

### Required (You Have These)
```bash
RESEND_API_KEY=re_xxxxx...              # ✅ Email sending
DATABASE_URL=postgresql://...       # ✅ Store messages
```

### Enable Cal (Choose One)
```bash
PHELAN_AUTONOMY_ENABLED=1              # Direct enable
# OR
ENABLE_SCHEDULED_PHELAN_AUTONOMY=1     # Scheduler enable (default: 1)
```

### Optional Tuning
```bash
PHELAN_AUTONOMY_EVERY_HOURS=6          # Cycle frequency (default: 6)
PHELAN_AUTONOMY_DAILY_CAP=10           # Max sends/day (default: 10)
PHELAN_AUTONOMY_FIRST_RUN_DELAY_MINUTES=20  # Startup delay (default: 20)
```

### Learning Reports
```bash
ENABLE_SCHEDULED_PHELAN_COMM_LEARNING=1  # Enable reports (default: 1)
ADMIN_EMAIL=your@email.com            # Where reports go
```

### Other Flags (Optional)
```bash
PHELAN_BUYER_SALES_ENABLED=0           # Robot sales intros (default: 0, Jobs focus)
REDIS_URL=redis://...               # Runtime toggles (should be set)
```

---

## Deployment Steps

### 1. Set the Secret
```bash
fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot
```

This will:
- Trigger a redeploy
- Worker process will start Phelan autonomy thread
- First cycle runs after 20min warm-up

### 2. Verify It Started
Check logs:
```bash
fly logs -a ready-2-robot | grep cal-autonomy
```

Look for:
```
[phelan-autonomy] scheduler thread started
```

### 3. Monitor First Cycle
After ~20 minutes:
```bash
fly logs -a ready-2-robot | grep "Phelan autonomy cycle"
```

Should see:
```
Phelan autonomy cycle: status=... drafted=N sent=N
```

### 4. Check Phelan Data (After 24-48h)
Visit admin panel or check outreach:
```bash
# On Fly console:
fly ssh console -a ready-2-robot

# Check recent sends:
python3 -c "
from app.database import SessionLocal
from app.models.outreach import OutreachMessage
from datetime import datetime, timezone, timedelta

db = SessionLocal()
since = datetime.now(timezone.utc) - timedelta(hours=24)
count = db.query(OutreachMessage).filter(
    OutreachMessage.sent_at >= since
).count()
print(f'Sends last 24h: {count}')
"
```

---

## Safety Features

### Daily Send Cap
Default: 10 sends/day
- Conservative start for new angles
- Protects sender reputation
- Increase after patterns prove out

### Bounce Protection
If bounce rate > 5% (trailing 7d):
- Pauses new intros
- Follow-ups continue
- Auto-resumes when rate drops

### Deliverability Gates
- Hunter confidence thresholds
- Address validation
- Domain reputation checks

---

## Troubleshooting

### "Phelan autonomy disabled" in logs
- Check `PHELAN_AUTONOMY_ENABLED` is set
- Or check `ENABLE_SCHEDULED_PHELAN_AUTONOMY` isn't set to 0
- Try Admin panel runtime toggle

### "No hot leads" / Zero sends
- Cal only sends to qualified leads
- Check lead scoring pipeline
- Verify CRM has accounts with score > threshold

### "Resend API error"
- Verify `RESEND_API_KEY` is valid
- Check Resend dashboard for issues
- Verify sender domain is configured

### Phelan still shows zero after enabling
- Allow 24-48h for first cycle + sends
- Check `communication_learning_report.py` logs
- Verify worker process is running (not just web)

---

## Expected Timeline

| Time | What Happens |
|------|-------------|
| T+0 | Set `PHELAN_AUTONOMY_ENABLED=1`, redeploy |
| T+20min | First Cal cycle runs |
| T+20min | First intro emails sent (up to 10) |
| T+6h | Second cycle (more sends if under daily cap) |
| T+24h | Should see ~10-40 sends |
| T+7d | First Phelan learning report |

---

## Next Steps

1. **Now:** Run `fly secrets set PHELAN_AUTONOMY_ENABLED=1 -a ready-2-robot`
2. **In 30min:** Check logs for "Phelan autonomy cycle" success
3. **Tomorrow:** Verify Admin panel shows outreach activity
4. **Next week:** Review first Phelan learning report

---

## Files Reference

- `app/services/cal_autonomy.py` - Autonomous sending logic
- `app/services/communication_learning_report.py` - Phelan reports
- `app/services/agent_messaging.py` - Buyer variants (angles)
- `app/main.py` - Scheduler startup (lines 897-957)
- `app/api/admin_extended.py` - Admin runtime toggle
