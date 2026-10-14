# Audit: Jobs/Employment/Supply-Side References

**Date**: 2026-10-14  
**Scope**: AGENTS.md, docs/, .cursor/, and agent-facing config  
**Purpose**: Identify every place that defines RFR as a jobs, Job Cards, or employment product, or that brings in supply-side or hiring data

---

## Category 1: Product Definition as "Employment Layer" / "Job Cards"

### AGENTS.md

**Line 10**: 
> ReadyForRobots is **recruitment and placement infrastructure for robotic labor**. The unit of value is the **Robot Job**.

**Line 15**:
> Customers register a robot as available for work and receive jobs it is qualified to perform.

**Line 16**:
> They keep those jobs in **native CRM** (`/pipeline?src=jobs_activate`) or HubSpot.

**Line 21 (table)**:
| **Activation** | Does this move URL → Job Cards → signup → unlocked jobs in CRM? |

**Line 23 (table)**:
| **CRM path** | Does Jobs CRM stay on jobs (not SIGNAL buyers)? |

**Line 24 (table)**:
| **Trust** | Are Job Cards real work with named employers, not invented economics? |

**Line 26 (table)**:
| **Value proof** | Can an anonymous user see a Robot Job Card before signup? |

**Line 28**: "Lead-quality north star (below) is **SIGNAL infrastructure**, not the product."

**Line 31**: "Do not hop Jobs traffic onto HOT buyers."

**Line 33**: "**Hermes is retired** ... The product loop is robot URL → Job Cards"

**Line 41**: "The experiment is now the product: **`/` = Jobs terminal**"

**Line 186**: "See [product_market_fit.md] ... Agents must drive robot URL → Job Cards → CRM unlock."

---

### docs/market_thesis.md

**Line 13**:
> **Recruitment and placement infrastructure for robotic labor.** The unit of value is the Robot Job. Operating model: [robot_employment_model.md](./robot_employment_model.md).

**Line 15**:
> We win on **job requirements ↔ robot capabilities**, not company count.

**Line 17**:
> Supply-side roster: [robot_employment_universe.md](./robot_employment_universe.md)

**Line 19**:
> Hero: **Find jobs for your robot. Robots need jobs. We find the work.**

**Line 21**:
> Current experiment: five evidence-backed machine-tending Job Cards for RobCo

**Line 186**:
> Agents must drive robot URL → Job Cards → CRM unlock. Do not hop onto SIGNAL buyers.

---

### docs/product_market_fit.md

Referenced by AGENTS.md but not audited in detail. Likely defines Jobs/employment model.

---

### docs/robot_employment_model.md

Referenced by market_thesis.md and AGENTS.md. Title and references suggest it defines the "employment layer" concept.

**Line 4** (from grep):
> `/` Jobs terminal — FIND → QUALIFY → PLACE later

---

### docs/EXPERIMENT_MODE.md

Referenced by AGENTS.md.

**Line 9**:
> The experiment **became the product**. The live surface is **`/`** (Jobs terminal)

---

### docs/CAPABILITY_MODEL.md

Referenced by AGENTS.md ("Read `docs/CAPABILITY_MODEL.md`").

---

### docs/value_first_principle.md

Referenced by AGENTS.md and new CLAUDE.md.

**Line 22** (from grep):
> employer, workplace, work being performed (context: likely Job Card structure)

---

## Category 2: Jobs CRM / Jobs Product References

### docs/cal_persona_spec.md

**Line 3**:
> Cal's **job** is the Jobs CRM desk after Open CRM.

**Line 10**:
> read the desk, save task-model source vs self-train, prepare the apply draft.

---

### docs/cal_floor_manager_log.md

**Line 188**:
> Pipeline tier scoring still broken — 5 leads, all tier_none, HOT=0 for 25th tick. (Context: discusses CRM tiers)

---

### docs/TRAFFIC_SPRINT.md

**Line 40**:
> **Find Jobs for Robots.**

**Line 104**:
> *Find jobs for your robot.*

**Line 109**:
> *Find jobs for the robots you sell.*

---

### docs/product_sim/OVERNIGHT_SCRUB_QUALIFY_TEMPLATE.md

**Line 112**:
> *Find jobs for your robot.*

---

### docs/product_sim/worksite/ROBOT_DIRECTED_DISCOVERY.md

**Line 26**:
> *Find jobs for my robot* — not *Map America's DCs*.

---

### docs/robot_understanding_v1.md

**Line 458**:
> `POST /api/robot-profile` · UI: `/` Jobs terminal left rail = profile, right = jobs.

---

### docs/agent-product-manager.md

**Line 12**:
> (Blank context line from grep — likely discusses Jobs terminal)

---

### docs/jobs_crm.md

Referenced by AGENTS.md. Defines "Jobs CRM spec (signup wall, free 5 / 15×month / 7-day, export)".

---

## Category 3: Supply-Side / Hiring Data References

### docs/robot_employment_universe.md

Referenced by market_thesis.md as "supply-side roster".

---

### docs/grace_gong_hiring_list_integration.md

**DELETED** in Grace Gong removal PR #313.

**Line 106** (pre-deletion):
> **Less immediate relevance to Jobs product (e.g., defense, compute hardware)

---

### docs/robot_opportunity_sources.csv

**Lines 3-13**:
Multiple rows referencing job boards (Amazon jobs, Adzuna, Jooble) with queries like:
- "robotics technician"
- "amazon robotics"
- "autonomous mobile robot technician"

These appear to be **people-hiring job board sources**, not buyer intent sources.

---

### docs/rfr_intelligence_architecture.md

**Line 169**:
> third-shift forklift hiring → reconstruct pallet flow → high Work Match → CALL NOW

(Context: appears to be describing a workflow reconstruction engine, but mentions "hiring" in passing)

---

## Category 4: .cursor/ Skills and Agent Config

### .cursor/skills/verify-readyforrobots/SKILL.md

**Line 3**:
> Drive ReadyForRobots Jobs the way a user does — FIND on `/`, Job Cards, Jobs chrome, Jobs CRM, About.

**Line 8**:
> Primary surface: **Jobs web UI** on `https://readyforrobots.com`

**Line 10**:
> `/` is FIND (`/?visit=jobs` is the same document). Jobs proof is this skill plus `POST /api/robot-job-search`

**Line 12**:
> **No Jobs product PR without pstack release checks.**

**Line 32**:
> Match `POST /api/robot-job-match` is the Jobs FIND path and does not write CRM.

**Line 53**:
> That JS contains `Find jobs for your robot`, `Jobs for`, and `jobs_activate`

**Lines 74-75** (smoke test table):
| find-jobs | `POST /api/robot-job-match` (Vega profile or chip) | `state=matches`, `job_count>0`, job titles |
| find-url | `POST /api/robot-job-search` (Dexmate + Greenfield) | not Research failed / Failed to fetch |

**Line 85**:
> FIND form: `aria-label="Find jobs for your robot"`

---

### .cursor/skills/verify-readyforrobots/features/jobs-crm.md

**Line 3**:
> Step 03 is **CRM**. Checking a job on step 02 dumps it into this desk. Kept Job Cards land on `/pipeline?src=jobs_activate`

**Line 28**:
> Session path (browser). Open `/pipeline?src=jobs_activate` with a handoff. Headline **CRM**. Process bar 03 current. Listing of jobs they kept

---

### .cursor/skills/verify-readyforrobots/features/jobs-chrome.md

**Line 8**:
> `chrome-process` FIND has no 01 / 02 / 03 process bar. Clicking a job card must not remount it.

**Line 11**:
> `chrome-pstack` How / Act / Critic is the **release gate** (`scripts/pstack_release.py`), not a required banner on `/`. Matcher is `POST /api/robot-job-match`.

**Line 26**:
> **JS canary (CI).** Run `python3 scripts/agent_verify.py drive --feature jobs-chrome`. Live `/` bundle: `Find jobs for your robot`, `jobs_activate`.

---

### .cursor/skills/verify-readyforrobots/features/find-jobs.md

**Line 3**:
> Find jobs lets an OEM or distributor paste a robot product URL (or pick a robot type) on `/` and see named Robot Jobs before signup.

**Line 7**:
> `find-open` shows FIND on `/` (and `/?visit=jobs`) with headline, URL field, and three live named-employer jobs as inline text.

**Line 10**:
> `find-api` is the same path the UI calls (`POST /api/robot-job-match`).

**Line 17**:
> Submit the FIND form labeled `Find jobs for your robot`, or pick **What type of robot?** and **Find jobs →**.

---

### .cursor/skills/verify-readyforrobots/features/find-stay.md

**Line 11**:
> `employer-examine` opens a named catalog robot

**Line 18**:
> Open `https://readyforrobots.com/` and click **Jobs for Robots**, or load `/?visit=jobs`.

**Line 21**:
> Employer door: **Robots for Jobs** → match catalog robots → click a robot to examine it → post the job

---

## Category 5: Code/API References to Jobs/Employment

### pstack/README.md

**Line 10**:
> How → name the owner before editing FIND, Job Cards, CRM, or matching

**Line 33**:
> Class-picker click is a no-op (`Agtonomy` → Agriculture) | `qualifyActive` always POSTs `/api/robot-job-search`

**Line 38**:
> Live Critic posts `POST /api/robot-job-search` (the URL FIND actually calls)

**Line 43**:
> Matcher replacement (`app/services/robot_job_capability_match.py` stays code)

---

### CHATGPT.md

**Line 13**:
> ReadyForRobots finds jobs for robots.

**Line 36**:
> Find Jobs for Robots.

**Line 127**:
> ## 4. Robot Job match contract

**Line 139**:
> → ROBOT JOB REQUIREMENTS

**Line 196**:
> The relationship between a Robot Profile and Robot Job requirements.

**Line 214**:
> Find jobs for your robot.

**Line 371**:
> the operating system for robot employment.

**Line 472**:
> Avoid generic CRM/sales language when the Robot Job vocabulary is more

**Line 486**:
> Could my robot do this job?

---

## Category 6: Reports / Deployment Guides (Already in reports/)

These are generated artifacts and should not be committed per AGENTS.md, but they contain historical context:

- `reports/grace_gong_implementation_summary.md` — **DELETED in PR #313**
- `reports/semantic_extraction_progress.md`
- `reports/deployment_and_testing_guide.md`
- `WALKTHROUGH.md`
- `BUYER_READINESS_APPLIED.md`
- `BUYER_READINESS_FIXES_APPLIED.md`
- `DAILY_BUYERS_EMAIL_APPLIED.md`
- `REBUILD_ROBOT_JOBS.md`
- `OPEN_ITEMS_PRIORITY.md`
- `TESTING_QUICKSTART.md`
- `SOCIAL_MEDIA_COPY.md`

---

## Summary by File Type

### Critical (Agent-facing, loaded on every session)

| File | Status | Jobs/Employment Refs |
|------|--------|---------------------|
| **AGENTS.md** | ❌ Needs rewrite | 15+ refs to "Job Cards", "employment layer", "Jobs terminal", "Jobs CRM" |
| **CLAUDE.md** | ✅ Fixed | Replaced with corrected version |
| **docs/market_thesis.md** | ❌ Needs rewrite | 8+ refs to "Robot Job", "job requirements", "Find jobs for your robot" |
| **docs/product_market_fit.md** | ⚠️ Not audited | Referenced by AGENTS.md, likely defines Jobs model |
| **docs/robot_employment_model.md** | ❌ Needs review | Title suggests employment framing |
| **docs/EXPERIMENT_MODE.md** | ❌ Needs review | "Jobs terminal" |
| **docs/CAPABILITY_MODEL.md** | ⚠️ Not audited | Referenced by AGENTS.md |
| **docs/value_first_principle.md** | ✅ Likely OK | Only mentions Job Card structure in passing |

### Skills (.cursor/skills/)

| File | Status | Jobs/Employment Refs |
|------|--------|---------------------|
| **verify-readyforrobots/SKILL.md** | ❌ Needs rewrite | 10+ refs to "Jobs", "Job Cards", "find jobs for" |
| **verify-readyforrobots/features/jobs-crm.md** | ❌ Needs rewrite | Entire file about "Jobs CRM" |
| **verify-readyforrobots/features/jobs-chrome.md** | ❌ Needs rewrite | "jobs-chrome" feature |
| **verify-readyforrobots/features/find-jobs.md** | ❌ Needs rewrite | "Find jobs" feature |
| **verify-readyforrobots/features/find-stay.md** | ❌ Needs rewrite | "Jobs for Robots" |

### Documentation (docs/)

| File | Status | Jobs/Employment Refs |
|------|--------|---------------------|
| **docs/robot_opportunity_sources.csv** | ⚠️ Check | Job board sources (amazon.jobs, Adzuna, Jooble) |
| **docs/cal_persona_spec.md** | ❌ Needs review | "Jobs CRM desk" |
| **docs/jobs_crm.md** | ❌ Exists | Entire file about Jobs CRM spec |
| **docs/robot_employment_universe.md** | ❌ Exists | "supply-side roster" |
| **docs/TRAFFIC_SPRINT.md** | ❌ Needs review | "Find Jobs for Robots" |
| **pstack/README.md** | ⚠️ Check | References "Job Cards", CRM, matching |
| **CHATGPT.md** | ⚠️ Check | "finds jobs for robots", "robot employment" |

### Reports / Guides (root *.md files)

Most are deployment walkthroughs or historical context. Should not be loaded by agents. Several reference "job board scraper" as the old system.

---

## Recommended Actions

1. **AGENTS.md**: Full rewrite of product definition section (lines 10-186) to match new CLAUDE.md framing
2. **docs/market_thesis.md**: Remove employment/job language, reframe as buyer intelligence
3. **docs/product_market_fit.md**: Audit and likely rewrite
4. **docs/robot_employment_model.md**: Archive or rewrite as "robot taxonomy classification"
5. **docs/EXPERIMENT_MODE.md**: Update to "buyer discovery" instead of "Jobs terminal"
6. **docs/CAPABILITY_MODEL.md**: Audit (not yet checked)
7. **docs/jobs_crm.md**: Rename to "buyer_pipeline.md" or similar
8. **docs/robot_employment_universe.md**: Archive (supply-side)
9. **.cursor/skills/verify-readyforrobots/**: Rewrite all features to use "buyer opportunities" instead of "Job Cards"
10. **docs/robot_opportunity_sources.csv**: Audit job board sources (amazon.jobs, etc.) — are these buyer intent or people-hiring?

---

**Files Not Audited** (require manual review):
- `docs/product_market_fit.md`
- `docs/CAPABILITY_MODEL.md`
- `docs/competitive_positioning.md` (referenced but not in grep results)
- `docs/conversion_agent_challenges.md`
- `docs/lead_quality_north_star.md`
- Any other docs/ files not caught by the grep patterns
