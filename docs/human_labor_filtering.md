# Human Labor Filtering - Top 25 Robot Jobs

## Overview

The Daily Top 25 Robot Jobs report must only include jobs where **employers explicitly ask for robots**, not human labor positions that could potentially be automated.

## The Critical Distinction

### ✓ VALID Robot Job
**Employer is asking for a robot to do the work**
- "Need AMR for warehouse pallet transport"
- "Seeking autonomous floor scrubber for night cleaning"
- "Looking for robotic picker for DC operations"
- "Cobot needed for machine tending"

### ✗ INVALID Human Labor
**Employer is hiring a person to do the work**
- "Warehouse Associate - Pick/Pack - $18/hr - Benefits"
- "Housekeeper Needed - Full Time - Apply Today"
- "Machine Operator - 2nd Shift - Experience Required"
- "Order Picker - Forklift Certified - Hiring Now"

## Filtering Logic

### Two-Stage Filter (app/services/robot_job_extract.py)

**Stage 1: Must explicitly mention robots**
```python
_ROBOT_ASK_RE = r"(?:robots?|robotic|robotics|cobots?|humanoids?|amrs?|agvs?|drones?)"
```

The posting MUST contain robot-related terms:
- robot, robotic, robotics
- cobot, humanoid
- AMR, AGV, drone

**Stage 2: Must NOT mention human hiring**
```python
_PERSON_HIRE_RE = r"(?:operators?|technicians?|engineers?|hiring|applying|full-time|...)"
```

The posting must NOT contain human employment language:
- Human roles: operator, technician, engineer, picker, housekeeper
- Hiring language: hiring, seeking, apply now, resume, interview
- Employment terms: full-time, part-time, position, benefits, salary
- Requirements: experience required, degree, certification, background check

### Filter in Daily Jobs (app/services/daily_jobs_report.py)

```python
def is_robot_automation_lead(title: str, *extra: str) -> bool:
    """True when the employer is asking for a robot. A human job is not enough."""
    from app.services.robot_job_extract import asks_for_a_robot
    return asks_for_a_robot(title, *extra)
```

Every job in the top 25 report must pass `is_robot_automation_lead()`.

### SQL Pre-filter

```python
def _robot_ask_clause():
    """SQL prefilter: the posting text names a robot."""
    needles = ("%robot%", "%cobot%", "%humanoid%", "%amr%", "%agv%", "%drone%")
    columns = (
        RobotJob.robot_compatible_task,
        RobotJob.observed_workflow,
        RobotJob.why_job,
    )
    return or_(*(column.ilike(needle) for column in columns for needle in needles))
```

Database query filters at SQL level before Python filtering.

## Examples

### ✓ Pass Filter (Valid Robot Jobs)

1. **"AMR for pallet transport in DC"**
   - Contains: "AMR" ✓
   - No human hiring language ✓
   - Result: VALID

2. **"Autonomous floor scrubber needed for warehouse cleaning"**
   - Contains: "autonomous" + "scrubber" ✓
   - No human hiring language ✓
   - Result: VALID

3. **"Hospital delivery robot for pharmacy transport"**
   - Contains: "robot" ✓
   - No human hiring language ✓
   - Result: VALID

### ✗ Fail Filter (Human Labor)

1. **"Warehouse Associate - Picker - $18/hr - Full Time"**
   - Contains robot terms: NO ✗
   - Result: INVALID (no robot mention)

2. **"Robotics Technician - Maintain AMR Fleet - Benefits"**
   - Contains: "robotics" + "AMR" ✓
   - Contains: "Technician" + "Benefits" ✗
   - Result: INVALID (hiring a person to work ON robots)

3. **"Order Picker Wanted - Apply Today - Hiring Now"**
   - Contains robot terms: NO ✗
   - Contains: "Hiring" + "Apply" ✗
   - Result: INVALID (human hiring language)

## Audit Process

### Manual Audit

Run the audit script to check current top 25:

```bash
# Dry run (shows what would be cleaned)
python3 scripts/audit_clean_top_25_jobs.py --dry-run

# Apply changes (mark human labor as not_robot_job)
python3 scripts/audit_clean_top_25_jobs.py --apply
```

### What the Audit Checks

1. **Explicit robot mention**: Must contain robot/cobot/humanoid/AMR/AGV/drone
2. **No human hiring indicators** (multiple must be present to flag):
   - Hiring language: "hiring", "seeking", "apply now"
   - Employment type: "full-time", "part-time", "position"
   - Benefits: "401k", "health insurance", "PTO"
   - Compensation: "hourly wage", "salary range", "$XX/hr"
   - Requirements: "experience required", "degree", "certification"
   - Process: "resume", "interview", "background check"

### Audit Output

```
AUDITING TOP 25 ROBOT JOBS FOR HUMAN LABOR
================================================================================

Retrieved 25 jobs from database

✓ CLEAN ROBOT JOBS: 23
✗ HUMAN LABOR CONTAMINATION: 2

================================================================================
HUMAN LABOR JOBS FOUND (NEED REMOVAL)
================================================================================

Rank  3: Amazon Fulfillment Center
  Title: Warehouse Associate - Picker
  Action: picking
  Reasons: hiring human workers, employment type for humans, human compensation
  Job Key: amz-dc-picker-123

Rank 17: Marriott Hotels
  Title: Housekeeper - Full Time
  Action: housekeeping
  Reasons: employment type for humans, human application process
  Job Key: marriott-hsk-456
```

## Cleanup Actions

When human labor is detected:

1. **Mark as not_robot_job**: Update `investigate_status = 'not_robot_job'`
2. **Exclude from reports**: Job won't appear in future top 25 emails
3. **Log reason**: Record why it was flagged

## Prevention

### Scraper Level

Job board scrapers already extract human labor positions (correct!) but filter them:

```python
# robot_job_extract.py extracts:
- order picker, housekeeper, cook, machine tender (✓ extract these)

# daily_jobs_report.py filters:
- Must ask for a robot explicitly (✓ only robot requests pass)
```

### Database Level

`robot_jobs` table stores ALL observed work (human AND robot), but daily report query filters:

```python
select_daily_report_rows():
    .filter(_robot_ask_clause())  # SQL level: must mention robot
    # Then Python level: asks_for_a_robot() must return True
```

## Monitoring

### Key Metrics

- **Contamination rate**: % of top 25 that are human labor (target: 0%)
- **Filter strictness**: How many valid robot jobs are caught (minimize false positives)
- **Coverage**: Are we missing robot requests due to overly strict filters?

### Weekly Check

```bash
# Run audit every Monday before daily report
python3 scripts/audit_clean_top_25_jobs.py --dry-run

# If contamination found, clean it
python3 scripts/audit_clean_top_25_jobs.py --apply
```

## Edge Cases

### Borderline Cases

1. **"Robot Operator Needed"**
   - Contains: "Robot" ✓
   - Contains: "Operator" ✗
   - Decision: INVALID (hiring person to operate robot, not buying robot)

2. **"AMR Maintenance Technician"**
   - Contains: "AMR" ✓
   - Contains: "Technician" ✗
   - Decision: INVALID (hiring person to maintain robots)

3. **"Autonomous Forklift for Warehouse"**
   - Contains: "Autonomous" (implies robot) ✓
   - No human hiring language ✓
   - Decision: VALID (asking for the machine)

### When in Doubt

**Rule**: If the employer is hiring a PERSON to do/operate/maintain something, it's NOT a robot job, even if robots are mentioned.

**Test**: Replace "robot" with "person" - does the sentence still make sense?
- "Need AMR for transport" → "Need person for transport" (✗ doesn't make sense) = ROBOT JOB ✓
- "AMR Operator Needed" → "Person Operator Needed" (✓ makes sense) = HUMAN JOB ✗

## Summary

**Goal**: Top 25 must be employers saying **"I need a robot to do this work"**, not **"I need a person to do this work"**.

**Approach**: 
1. Must explicitly mention robots (AMR, cobot, autonomous, etc.)
2. Must NOT have human hiring language (hiring, apply, resume, benefits, etc.)
3. Database stores all work; daily report filters aggressively

**Result**: Clean list of genuine robot opportunities, no human labor contamination.

---

**Related Files**:
- `app/services/robot_job_extract.py` - Core filtering logic
- `app/services/daily_jobs_report.py` - Top 25 report generation
- `scripts/audit_clean_top_25_jobs.py` - Audit and cleanup tool
