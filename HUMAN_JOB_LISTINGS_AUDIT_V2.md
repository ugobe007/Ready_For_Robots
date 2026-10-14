# Audit v2: Human Job Listings References

**Date**: 2026-10-14  
**CLAUDE.md version**: v2  
**Scope**: AGENTS.md, docs/, .cursor/

## CLAUDE.md v2 Definitions (CORRECT)

Under v2, these are **correct** and should NOT be changed:
- ✅ "robot jobs" = jobs FOR robots (workflows at companies that robots could do)
- ✅ "Job Cards" = cards showing robot job opportunities
- ✅ "Jobs CRM" = CRM for managing robot job opportunities
- ✅ "find jobs for your robot" = find workflows for your robot to perform
- ✅ "Jobs product" = product that finds robot jobs

## What to Flag

Flag ONLY:
1. **"jobs" meaning human job listings** (people-hiring postings)
2. **Indirect sources treated as authoritative** (not signals attached to buyers)
3. **Supply-side hiring in market_thesis.md** (should be in docs/signals/supply_side_hiring.md)

---

## 1. Human Job Listings / Job Boards

### docs/robot_opportunity_sources.csv

**Lines 2-200+**: Multiple rows querying job board APIs for **people-hiring** roles:

```csv
amazon.jobs,query=rme technician,Logistics
amazon.jobs,query=robotics technician,Logistics
amazon.jobs,query=automation technician,Logistics
adzuna.com/api/jobs,what=AMR technician warehouse,Logistics
jooble.org/api,keywords=robotics technician distribution center,Logistics
```

**Issue**: These are people-hiring job boards. Under v2, robotics/automation hiring at **potential buyers** (e.g., a warehouse hiring "AMR technician") is a **readiness signal** attached to that company's robot job opportunity—not a lead source by itself.

**Recommendation**:
- Keep the buyer-side queries (warehouse hiring AMR tech = signal that warehouse is deploying AMRs)
- Tag them clearly as "robotics hiring signal" not "robot job source"
- Remove queries for jobs at robot makers (supply-side)
- Map each detected role to a taxonomy workflow + industry
- Attach as signal on the company's opportunity

---

### docs/reference/rfr_cursor_package/frontend/pages/HowItWorks.tsx

**Line 31**:
```tsx
{ icon: Briefcase, label: "Job Postings", sub: "LinkedIn · Indeed · ZipRecruiter" }
```

**Issue**: UI copy suggests RFR scrapes people-hiring job boards as the product.

**Recommendation**: If this is explaining readiness signals, update copy to clarify: "Robotics Hiring Signals" or "Automation Role Postings (readiness indicator)". If it's legacy UI, archive or update.

---

### docs/reference/rfr_cursor_package/frontend/pages/Signals.tsx

**Line 71**:
```tsx
["LinkedIn", "Indeed", "Glassdoor", "Company career pages"]
```

**Issue**: Same as above—lists job boards without clarifying they're signals, not the product.

**Recommendation**: Add context that these detect robotics hiring as a readiness signal.

---

## 2. Indirect Sources Treated as Authoritative

### docs/market_thesis.md (Grace Gong section)

**Lines 49-93** (now deleted in PR #313, but needs to be **moved**, not deleted):

> ## Market Intelligence: Grace Gong Physical AI Hiring List (2026-10-11)
> 
> **Source:** Grace Gong "On My Radar" Week 98 — 36 physical AI companies actively hiring...
> 
> **Strategic signal:** These are **deployment-active companies** scaling through hiring...

**Issue**: Supply-side hiring (robot makers hiring) was in `market_thesis.md` and treated as "deployment-active companies" (implying they're buyers).

**Recommendation** (per user):
- Move to `docs/signals/supply_side_hiring.md`
- Label clearly: "market context only — not a buyer source"
- Keep scripts but confirm they never add robot makers to buyer pipeline

---

## 3. Other References (Likely OK)

### docs/product_sim/worksite/ROBOT_DIRECTED_DISCOVERY_V2.md

**Line 46**:
> Human Job → Robot Job.

**Context**: Appears to be describing workflow translation (human task → robot-automatable task). This is **correct** under v2.

---

### docs/product_sim/envelopes/*.md

Multiple references to human job titles like "Order Selector", "EVS Floor Technician" in workflow translation context.

**Context**: These appear to be workflow reconstruction examples (human role → robot-automatable workflow). **Correct** under v2 if used to identify robot job opportunities.

---

## Summary

### Files Needing Changes

| File | Issue | Action |
|------|-------|--------|
| **docs/robot_opportunity_sources.csv** | Job board queries for people hiring | Keep buyer-side queries as "robotics hiring signals"; tag clearly; remove supply-side |
| **docs/market_thesis.md** | Grace Gong supply-side hiring section | Move to docs/signals/supply_side_hiring.md |
| **docs/reference/.../HowItWorks.tsx** | "Job Postings" UI copy | Clarify as "Robotics Hiring Signals (readiness)" |
| **docs/reference/.../Signals.tsx** | Job board list without context | Add signal context |

### Files That Are Fine

Most "Jobs CRM", "Job Cards", "find jobs for your robot" references are **correct** under v2 and need no changes.

---

## Proposed Buyer-Side Robotics Hiring Signal

Per user request, outline (don't build yet):

**Goal**: Detect robotics/automation job titles at **non-robot-maker companies**, map each to taxonomy workflow + industry, attach as readiness signal.

**Example**:
- **Company**: FedEx Ground (logistics, non-robot-maker)
- **Detected role**: "AMR Fleet Manager" (posted on LinkedIn)
- **Mapping**: 
  - Workflow: `picking_packing_palletizing` or `delivery_transport`
  - Industry: `warehouse_distribution`
- **Signal**: Attach to FedEx's robot job opportunity in warehouse_distribution workflow with confidence based on role seniority and recency

**Differentiation from supply-side**:
- ✅ Buyer signal: Hospital hiring "Robotic Surgery Coordinator" → hospital workflow signal
- ❌ Supply-side: Intuitive Surgical hiring "Robotics Engineer" → market context only

**Implementation sketch**:
1. Query job boards for robotics/automation roles (existing queries in robot_opportunity_sources.csv)
2. Filter: company is NOT in robot maker index
3. Parse role title → map to taxonomy function + industry
4. Attach as `robotics_hiring` signal on company's opportunity
5. Score by role seniority, posting date, count of related roles

**Next**: User approval before building.
