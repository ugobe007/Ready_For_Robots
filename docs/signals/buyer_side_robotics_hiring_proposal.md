# Proposal: Buyer-Side Robotics Hiring Signal

**Status**: Proposal only - not implemented  
**Category**: Readiness signal (indirect)  
**Date**: 2026-10-14

## Summary

Detect robotics and automation job postings at **non-robot-maker companies**, map each role to a taxonomy workflow + industry, and attach as a readiness signal on that company's robot job opportunity.

## Problem

Grace Gong's lists showed that tracking robotics hiring is valuable, but they tracked the **wrong side**: robot makers (supply) instead of potential buyers (demand).

**The insight**: When a *potential buyer* hires robotics or automation roles, that signals they plan to deploy robots.

## Examples

### ✅ Buyer-Side Signals (What We Want)

| Company | Role | Mapping | Signal Strength |
|---------|------|---------|----------------|
| **FedEx Ground** (logistics) | "AMR Fleet Manager" | workflow: `picking_packing_palletizing`<br>industry: `warehouse_distribution` | High (dedicated fleet role) |
| **Mayo Clinic** (healthcare) | "Robotic Surgery Coordinator" | workflow: `surgery_assistance`<br>industry: `hospital` | High (operational role) |
| **Marriott Hotels** | "Robotics Operations Lead" | workflow: `delivery_transport` or `cleaning`<br>industry: `hotel_resort` | Medium (exploratory) |
| **Amazon Warehouses** | "Automation Engineer - Robotics" | workflow: multiple<br>industry: `warehouse_distribution` | Medium (engineering support) |

### ❌ Supply-Side (What to Exclude)

| Company | Role | Why Excluded |
|---------|------|--------------|
| Intuitive Surgical | "Robotics Engineer" | Robot maker, not buyer |
| Boston Dynamics | "Field Applications Engineer" | Robot maker, not buyer |
| ABB Robotics | "Controls Engineer" | Robot maker, not buyer |

## Data Sources

Already in `docs/robot_opportunity_sources.csv`:

```csv
amazon.jobs,query=rme technician,Logistics
amazon.jobs,query=robotics technician,Logistics
amazon.jobs,query=automation technician,Logistics
adzuna.com/api/jobs,what=AMR technician warehouse,Logistics
jooble.org/api,keywords=robotics technician distribution center,Logistics
```

**Current issue**: These queries don't distinguish buyer-side from supply-side.

## Implementation Design

### Step 1: Query Job Boards

Use existing `robot_opportunity_sources.csv` queries, but add role-level filtering.

**Target roles**:
- Robotics Program Manager
- Automation Engineer (deployment/operations focus)
- AMR Fleet Manager / Coordinator
- Robotic [Process] Coordinator (surgery, food prep, etc.)
- Robotics Operations Lead / Director

**Exclude titles**:
- Software Engineer (too broad)
- Robotics Engineer at robot makers
- Sales / Marketing roles

### Step 2: Company Classification

For each detected role:
1. Extract company name and domain
2. Check against robot maker index (supply-side)
3. If robot maker → skip (supply-side context only)
4. If non-robot-maker → proceed (buyer-side signal)

### Step 3: Role → Taxonomy Mapping

Parse role title + job description → map to:
- **Workflow** (one of 13 taxonomy functions)
- **Industry** (one of 29 taxonomy industries)
- **Confidence** (based on role specificity)

**Mapping rules**:

| Role Pattern | Workflow | Industry | Confidence |
|--------------|----------|----------|------------|
| "AMR Fleet Manager" | `picking_packing_palletizing` or `delivery_transport` | From company industry | 0.8 |
| "Robotic Surgery Coordinator" | `surgery_assistance` | `hospital` | 0.9 |
| "Automation Engineer - Food Production" | `food_prep` or `machine_tending_assembly` | `food_manufacturing` | 0.7 |
| "Robotics Operations Lead" (vague) | TBD from description | From company | 0.5 |

### Step 4: Attach as Signal

Store in `signals` table or attach to company opportunity:

```python
{
  "signal_type": "robotics_hiring",
  "company_id": <company_id>,
  "workflow": "picking_packing_palletizing",
  "industry": "warehouse_distribution",
  "role_title": "AMR Fleet Manager",
  "role_seniority": "manager",  # coordinator < manager < director < vp
  "posted_date": "2026-10-01",
  "confidence": 0.8,
  "source": "linkedin_jobs",
  "evidence_url": "https://linkedin.com/jobs/view/..."
}
```

### Step 5: Scoring & Ranking

Weight signals by:
- **Role seniority**: Director/VP > Manager > Coordinator > Engineer
- **Role specificity**: "AMR Fleet Manager" > "Automation Engineer"
- **Recency**: Last 30 days = 1.0, 30-90 days = 0.7, 90+ days = 0.4
- **Count**: Multiple related roles = higher confidence

**Combined with other signals**:
- RFP published: 0.9
- Robotics hiring (director-level): 0.7
- Capex mentioned: 0.6
- Labor pressure signal: 0.5

## Database Schema

**Option A**: Add to existing `signals` table

```sql
ALTER TABLE signals ADD COLUMN workflow VARCHAR(100);
ALTER TABLE signals ADD COLUMN role_seniority VARCHAR(50);
ALTER TABLE signals ADD COLUMN role_title TEXT;
```

**Option B**: New `robotics_hiring_signals` table

```sql
CREATE TABLE robotics_hiring_signals (
  id SERIAL PRIMARY KEY,
  company_id INTEGER REFERENCES companies(id),
  workflow VARCHAR(100),  -- taxonomy function
  industry VARCHAR(100),  -- taxonomy industry
  role_title TEXT,
  role_seniority VARCHAR(50),
  posted_date DATE,
  confidence REAL,
  source VARCHAR(100),
  evidence_url TEXT,
  extracted_at TIMESTAMP DEFAULT NOW()
);
```

## Testing Plan

1. **Precision test**: Run on 50 known buyers with robotics roles → confirm no robot makers slip through
2. **Recall test**: Check if major robot buyers (Amazon, FedEx, Walmart) are detected
3. **Mapping accuracy**: Manual review of 50 role → workflow+industry mappings

## Success Metrics

- **Precision**: % of detected signals that are true buyer-side (target: >90%)
- **Mapping accuracy**: % of roles correctly mapped to workflow+industry (target: >80%)
- **Coverage**: % of known robot-deploying companies with hiring signal (target: >50%)

## Implementation Estimate

**Phase 1 (MVP)**: 
- Adapt existing job board queries with company filtering
- Simple role title → taxonomy mapping (rule-based)
- Attach to company opportunities
- ~8-12 hours

**Phase 2 (Enhanced)**:
- LLM-based role description → taxonomy mapping
- Seniority extraction
- Confidence scoring with multiple factors
- ~16-24 hours

## Risks & Mitigation

**Risk 1**: Robot makers slip through company filter
- **Mitigation**: Maintain curated robot maker index; manual review of high-volume employers

**Risk 2**: Role titles are ambiguous (e.g., "Automation Engineer")
- **Mitigation**: Require job description parsing; confidence scoring; manual spot-checks

**Risk 3**: Job board APIs rate-limit or change
- **Mitigation**: Use multiple sources; cache results; graceful degradation

## Related Documents

- [docs/signals/supply_side_hiring.md](supply_side_hiring.md) — Supply-side hiring (robot makers)
- [HUMAN_JOB_LISTINGS_AUDIT_V2.md](../../HUMAN_JOB_LISTINGS_AUDIT_V2.md) — Audit flagging current job board usage
- [tests/fixtures/taxonomy.v1.json](../../tests/fixtures/taxonomy.v1.json) — Taxonomy for workflow/industry mapping
- [CLAUDE.md](../../CLAUDE.md) — Product definition (robotics hiring as signal)

## Next Steps

1. **User approval** of this proposal
2. **Phase 1 implementation**: Build MVP with rule-based mapping
3. **Test** on 100 companies
4. **Iterate** based on precision/recall results
5. **Phase 2**: Add LLM-based mapping if needed

---

**Status**: Awaiting user approval before building.
