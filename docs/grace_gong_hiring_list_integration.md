# Grace Gong Physical AI Hiring List - Integration Guide

## Overview

Grace Gong publishes weekly "On My Radar" lists of physical AI companies ranked by hiring velocity (% headcount growth in past 90 days). This is a high-signal source for:

1. **Deployment evidence** — Companies scaling through hiring are deploying robots
2. **Job posting intelligence** — Career pages reveal what roles/verticals are active
3. **Market movement tracking** — Weekly cadence shows category velocity

**Current ingestion:** Week 98 (October 2026) — 36 companies

## Files Created

| File | Purpose |
|------|---------|
| `scripts/ingest_grace_gong_hiring_list.py` | Main ingestion script with company data |
| `app/services/grace_gong_career_pages.py` | Career page monitoring configuration |
| `reports/grace_gong_week_98_intelligence.md` | Generated intelligence report |
| `reports/grace_gong_week_98_intelligence.json` | Structured data export |
| `docs/market_thesis.md` | Updated with market intelligence section |

## Integration Tasks

### ✅ Completed

1. **Intelligence ingested** — 36 companies with metadata (category, location, career page)
2. **Market thesis updated** — New section in `docs/market_thesis.md` with strategic analysis
3. **Career pages cataloged** — `app/services/grace_gong_career_pages.py` with priority rankings

### 🔲 Pending (requires database access)

1. **Cross-reference with database** — Identify which companies already exist in `companies` table
2. **Add new companies** — Insert missing companies with source tag `grace_gong_week_98`
3. **Tag hiring activity** — Mark companies with `hiring_activity_signal: true` metadata
4. **Create scraper targets** — Add 36 career pages to scraping rotation

### 🔲 Recommended Next Steps

1. **Weekly automation** — Set up LinkedIn monitoring for Grace Gong's posts
2. **Career page scraping** — Implement job posting extraction from career pages
3. **Deployment correlation** — Track which hiring companies announce deployments
4. **Jobs matching integration** — Surface these companies in Jobs product as employers

## Usage Examples

### Run the ingestion script

```bash
# Dry run (no database changes)
python3 scripts/ingest_grace_gong_hiring_list.py --dry-run

# Apply to database (when DATABASE_URL is configured)
python3 scripts/ingest_grace_gong_hiring_list.py --apply
```

### Use the career pages config

```python
from app.services.grace_gong_career_pages import (
    GRACE_GONG_WEEK_98_CAREER_PAGES,
    get_high_priority_targets,
    get_by_category,
    get_by_location
)

# Get high priority career pages to scrape first
high_priority = get_high_priority_targets()
print(f"Scraping {len(high_priority)} high-priority career pages...")

# Get all humanoid companies (direct ICP)
humanoid_companies = get_by_category("humanoid")
for company in humanoid_companies:
    print(f"{company['company']} - {company['url']}")

# Get Bay Area companies (local deployment signal)
bay_area = [e for e in GRACE_GONG_WEEK_98_CAREER_PAGES 
            if e['location'] in ['San Francisco', 'Sunnyvale', 'Palo Alto', 
                                   'Redwood City', 'San Mateo', 'Santa Clara']]
```

### Query the intelligence report

```bash
# View the markdown report
cat reports/grace_gong_week_98_intelligence.md

# Parse the JSON data
python3 -c "
import json
with open('reports/grace_gong_week_98_intelligence.json') as f:
    data = json.load(f)
print(f'Week: {data[\"week\"]}')
print(f'Companies: {len(data[\"companies\"])}')
print(f'Published: {data[\"published_date\"]}')
"
```

## Priority Rankings

Companies are prioritized based on:

- **Critical:** High visibility, active deployments, clear job categories (e.g., Figure, Apptronik, Path Robotics)
- **High:** Strong ICP fit, foundation models, Bay Area location (e.g., Physical Intelligence, XDOF, Maven Robotics)
- **Medium:** Standard monitoring targets
- **Low:** Less immediate relevance to Jobs product (e.g., defense, compute hardware)

**High/Critical priority companies:** 15 of 36 (42%)

## Category Insights

| Category | Count | Strategic Value |
|----------|-------|-----------------|
| **Humanoid** | 10 (28%) | Direct ICP for Jobs product — general-purpose robots need diverse job placements |
| **Foundation Model** | 8 (22%) | Deployment multiplier — one platform serves many robot types |
| **Industrial** | 4 (11%) | Clear job categories — welding, warehouse, factory automation |
| **Software** | 3 (8%) | Enablement layer — track but not primary ICP |
| **Other** | 11 (31%) | Home robots, defense, service, autonomous vehicles |

## Geographic Distribution

| Region | Companies | Focus |
|--------|-----------|-------|
| **Bay Area** | 9 (25%) | Dense deployment signal — high priority for local intelligence |
| **China** | 9 (25%) | Beijing + Shenzhen clusters — consider APAC expansion for Jobs |
| **Other US** | 9 (25%) | Austin, Pittsburgh, Columbus, Boston, San Diego |
| **International** | 9 (25%) | Europe (Germany, Italy, Switzerland, UK), Asia (Seoul, Singapore), Canada |

## Integration with Existing Systems

### Pipeline Process

1. **Ingest** — `scripts/ingest_grace_gong_hiring_list.py` creates company records
2. **Scrape** — Career pages scraped weekly (new scraper target type: `career_page`)
3. **Enrich** — Job postings → deployment signals → industry classification
4. **Surface** — Companies appear in Jobs product as employers posting work

### Lead Quality Pipeline

These companies are **supply-side intelligence** (robot makers), not buyer leads. Tag as:
- `company_type: "robotics_vendor"`
- `hiring_activity_signal: true`
- `grace_gong_week: 98`
- `source: "grace_gong_linkedin"`

### Jobs Product Integration

- **Employer database** — These companies can post jobs in our Jobs marketplace
- **Deployment evidence** — Hiring activity correlates with deployment announcements
- **Capability matching** — Track which robot types each company produces for matching

## Weekly Monitoring Setup

Grace Gong publishes weekly. Set up automation:

1. **LinkedIn monitoring** — RSS feed or manual check every Monday
2. **Automated ingestion** — Parse new lists, run `ingest_grace_gong_hiring_list.py`
3. **Delta reporting** — Compare week-over-week: new companies, category shifts, geo trends
4. **Alerts** — Notify when high-priority companies appear or disappear from list

## Success Metrics

Track effectiveness of this intelligence:

- **Coverage** — % of Grace Gong companies in our database
- **Career page scrape success rate** — How many URLs return valid job data
- **Deployment correlation** — % of hiring companies that announce deployments within 90 days
- **Jobs product surface** — How many appear as employers in Jobs marketplace
- **Match quality** — Do their job postings align with our robot capability model?

## Related Documentation

- `docs/market_thesis.md` — Market intelligence section
- `docs/deployment_evidence_engine.md` — How hiring signals feed deployment tracking
- `docs/robot_employment_model.md` — Jobs product strategy
- `docs/CAPABILITY_MODEL.md` — Robot capability matching
- `reports/grace_gong_week_98_intelligence.md` — Full analysis report

## Contact / Source

- **Author:** Grace Gong
- **Platform:** LinkedIn
- **Series:** "On My Radar" (weekly)
- **Current week:** 98 (October 2026)
- **LinkedIn:** https://www.linkedin.com/in/grace-gong
- **Podcast:** Venture with Grace
