# Phelan Communication Learning Diagnostic Report

**Date:** 2026-10-10 03:39 UTC  
**Status:** ⚠️ NO ACTIVITY - Zero tagged intro sends in last 7 days

---

## What is Phelan?

Phelan is the **communication learning system** that:
1. Tags every Cal intro email with a "trust-first angle" (variant)
2. Classifies replies as positive/negative/interested
3. Reports which narrative angles earn the most trust
4. Provides directional learning signal (not statistical A/B testing due to low volume)

**Key metrics tracked:**
- Delivered/Open rates (leading indicators)
- Reply rates by angle
- Positive vs negative sentiment
- Subject line patterns

---

## Why Zero Sends?

The report shows **0 tagged intro sends** because:

### 1. Cal Autonomy Not Running
- No outreach emails are being sent
- Phelan autonomy must be enabled for Phelan to have data

### 2. Missing Configuration (Local Environment)
```
RESEND_API_KEY: MISSING
PHELAN_AUTONOMY_ENABLED: not set
ENABLE_SCHEDULED_PHELAN_AUTONOMY: not set
DATABASE_URL: not available
```

### 3. Production Setup Required
Phelan runs on **production Fly** environment where:
- Phelan autonomy drafts and sends buyer intro emails
- Each send is tagged with `OutreachMessage.payload.variant_id`
- Replies are classified by `reply_classifier.py`
- Weekly reports aggregate performance

---

## Required Environment Variables

### For Cal to Send Emails:
```bash
RESEND_API_KEY=<your-key>              # Email sending
PHELAN_AUTONOMY_ENABLED=1                 # Enable autonomous outreach
REDIS_URL=<your-redis>                 # Runtime state
DATABASE_URL=<your-postgres>           # Store messages
```

### For Communication Learning:
```bash
ENABLE_SCHEDULED_PHELAN_COMM_LEARNING=1   # Enable learning reports (default: 1)
PHELAN_COMM_LEARNING_ENABLED=1            # Can disable if needed
ADMIN_EMAIL=<operator-email>           # Where to send reports
```

---

## How Phelan Works (When Active)

### 1. **Intro Sending** (`agent_messaging.py`)
- Cal drafts intro emails for hot leads
- Each email tagged with a variant (angle):
  - Trust-first narratives
  - Different value propositions
  - Various CTAs
- Sends via Resend API

### 2. **Reply Classification** (`reply_classifier.py`)
- Monitors inbox for replies
- Classifies intent: interested, meeting, pricing, not_a_fit, unsubscribe
- Assigns sentiment

### 3. **Weekly Learning Report** (`communication_learning_report.py`)
- Aggregates by angle
- Calculates delivered%, open%, reply%, positive%
- Identifies winning narratives
- Sent to operator email

---

## Activation Checklist

To get Phelan working:

### On Fly Production:
1. ✅ Set `RESEND_API_KEY` (already in Fly secrets per docs)
2. ✅ Set `REDIS_URL` (should be configured)
3. ✅ Set `DATABASE_URL` (should be configured)
4. ❓ Verify `PHELAN_AUTONOMY_ENABLED=1` or toggle in Admin
5. ❓ Verify `ADMIN_EMAIL` is set for reports
6. ❓ Check scheduled worker is running Cal cycles

### Verify:
```bash
# On Fly:
fly ssh console -a ready-2-robot

# Check config:
printenv | grep CAL_
printenv | grep RESEND_

# Check database for recent activity:
python3 -c "from app.models.outreach import OutreachMessage; print(OutreachMessage.query.count())"
```

---

## Why You See This Report with Zero Data

The **communication learning report is running** (you're seeing this output), but it has **no data to analyze** because:
- Phelan autonomy isn't sending emails, OR
- Emails are being sent but not tagged with angles, OR  
- This is a local/dev environment without production data

**Next step:** Check Fly production to see if Phelan autonomy is enabled and configured correctly.

---

## Related Files

- `app/services/communication_learning_report.py` - Report generation
- `app/services/cal_autonomy.py` - Autonomous sending
- `app/services/agent_messaging.py` - Buyer variants (angles)
- `app/services/reply_classifier.py` - Reply intent classification
- `app/models/outreach.py` - OutreachMessage, OutreachReply models

---

## Recommended Actions

1. **Verify production Fly environment has:**
   - RESEND_API_KEY set
   - PHELAN_AUTONOMY_ENABLED=1
   - REDIS_URL configured
   - Scheduled worker running

2. **Check Admin panel:**
   - https://readyforrobots.com/admin
   - Look for Cal autopilot toggle
   - Check recent outreach activity

3. **Monitor for 24-48 hours:**
   - Cal should start sending intros
   - Phelan will begin collecting data
   - Weekly report will show performance

4. **If still zero:**
   - Check logs for Phelan autonomy errors
   - Verify lead pipeline has hot buyers
   - Confirm email sending isn't blocked
