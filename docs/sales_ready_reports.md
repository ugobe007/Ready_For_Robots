# Sales-Ready Robot Job Opportunity Reports

This document describes the PDF-style sales intelligence report format for robot buyer opportunities.

## Overview

The sales-ready report format transforms raw buyer readiness data into clean, actionable intelligence cards matching the layout shown in `Robot_Buyer_Intelligence_Report_0911.pdf`.

## Key Features

### 1. Sales-Friendly Format
- **Stage-based sections**: "RFP Open" and "Exploring" sections
- **Company cards** with rank, industry, location
- **Job-focused language**: Primary workflows and robot types needed
- **Sales intelligence**: Timeline, budget, incumbent vendor status
- **Evidence quotes** with dates for credibility
- **Cross-sell opportunities**: "Likely Next" workflows

### 2. Information Extraction

#### Budget Parsing
Extracts budget amounts from evidence text:
- Patterns: `investing $60.0M`, `budget of $1.9B`, `EUR 200M`
- Normalizes to: `$60.0M`, `$1.9B`, `€200.0M`
- Supports: USD, EUR, GBP, CHF, CAD

#### Timeline Estimation
Infers project timelines based on:
- **Explicit dates**: "Q3 2025", "in 2026", "January 2027"
- **Stage-based estimates**:
  - RFP Open: "High-intent window (est. 45–120 days)"
  - Exploring/Piloting: "Capital program phase (est. 90–210 days)"
  - Expanding: "Expansion window (est. 60–180 days)"

#### Vendor/Incumbent Extraction
Identifies vendors from evidence text:
- Patterns: `incumbent: Locus`, `deploying with AutoStore`, `using GreyOrange robots`
- Cleans trailing noise: "robots", "systems", "solutions"

#### Robot Type Mapping
Maps 17 workflow categories to sales-friendly robot types:

| Workflow Category | Sales-Friendly Name |
|------------------|---------------------|
| `cleaning` | Floor cleaning robots |
| `restroom_sanitizing` | Sanitizing robots |
| `delivery_service` | Delivery and serving robots |
| `food_prep` | Kitchen and food-prep robots |
| `warehouse_amr` | Warehouse AMRs |
| `forklift` | Autonomous forklifts |
| `palletizing` | Palletizing robots |
| `inventory` | Inventory robots |
| `security` | Security robots |
| `concierge` | Concierge robots |
| `entertainment` | Entertainment robots |
| `laundry` | Laundry robots |
| `manufacturing` | Cobots and industrial robots |
| `healthcare_logistics` | Hospital logistics robots |
| `outdoor` | Outdoor robots |
| `last_mile` | Delivery robots |
| `humanoid` | Humanoid robots |

### 3. Card Format

Each opportunity card includes:

```
001  Disney Parks & Resorts
Entertainment & Hospitality · Orlando, FL
Job: Floor & surface cleaning; Delivery / room service
Robot Types: Floor cleaning robots; Delivery and serving robots
Schedule: Capital program phase (est. 90–210 days) | Has Robots: Yes — Restroom / sanitizing | Budget: $60.0M
Status: RFP (incumbent: Locus)
"Disney seeking AMR vendors for hotel operations across 25+ properties" (2026-09-11)
"RFP issued for autonomous delivery robots" (2026-09-15)
Likely Next: Security / patrol, Concierge / greeting
```

## Usage

### Standalone Script

Generate a sales report from buyer ranking data:

```bash
python3 scripts/generate_sales_report.py                     # Top 25 opportunities
python3 scripts/generate_sales_report.py --limit 50          # Top 50
python3 scripts/generate_sales_report.py --stage rfp_open    # Only RFP open
python3 scripts/generate_sales_report.py --output report.txt # Save to file
```

### Daily Email Report

Enable sales-ready format in daily buyer emails:

```bash
export DAILY_BUYERS_FORMAT=sales  # Use PDF-style format
export DAILY_BUYERS_FORMAT=standard  # Use original format (default)
```

When `DAILY_BUYERS_FORMAT=sales`, the plain-text email body uses the sales-ready card format matching the PDF layout.

### Programmatic API

```python
from app.services.sales_report import build_job_opportunity, format_sales_report_text
from app.services.daily_buyers_report import render_sales_ready_report

# From buyer readiness data
opp = build_job_opportunity(
    rank=1,
    company=company_obj,
    readiness=readiness_obj,
    signals=signal_list,
)

# From daily report data structure
text = render_sales_ready_report(report_dict)
```

## Implementation

### Core Modules

- **`app/services/sales_report.py`**: Core formatting logic
  - `extract_budget()`: Parse budget amounts from text
  - `extract_vendor()`: Extract incumbent vendor names
  - `extract_date_from_evidence()`: Extract publication dates
  - `estimate_timeline()`: Infer project timeline from stage + evidence
  - `build_job_opportunity()`: Build a JobOpportunity card from company/signals
  - `format_job_opportunity_text()`: Format card as plain text
  - `format_sales_report_text()`: Format full report with sections

- **`app/services/daily_buyers_report.py`**: Integration with daily reports
  - `render_sales_ready_report()`: Render report from buyer data
  - `_format_sales_card()`: Format one buyer as a sales card

- **`scripts/generate_sales_report.py`**: CLI for generating reports

### Tests

- **`tests/test_sales_report.py`**: Unit tests for extraction and formatting
- **`tests/test_sales_report_integration.py`**: Integration test with buyer data

All tests pass:
```bash
python3 -m pytest tests/test_sales_report*.py -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DAILY_BUYERS_FORMAT` | `standard` | Email body format: `standard` or `sales` |
| `DAILY_BUYERS_STAGES` | (all active) | Stages to include in report |
| `DAILY_BUYERS_REFRESH` | `1` | Re-score companies before report generation |

## Sales Intelligence Components

The report combines multiple data sources to build actionable sales cards:

1. **Buyer Stage** (from `buyer_ranking.py`): rfp_open, exploring, expanding, preparing
2. **Open Workflows** (from `opportunity_map.py`): Per-category intent status
3. **Deployed Robots** (from `opportunity_map.py`): What they already have
4. **Predicted Workflows** (from `opportunity_map.py`): High-confidence cross-sell targets
5. **Evidence Signals** (from database): Text snippets with dates and URLs
6. **Budget & Vendors** (extracted): Parsed from evidence text on the fly

## Comparison: Standard vs Sales-Ready Format

### Standard Format (DAILY_BUYERS_FORMAT=standard)
```
001  Disney Parks & Resorts  (Entertainment & Hospitality, Orlando, FL)
     Why: Published RFP for hotel robotics program  [score 95]
     ▸ Floor & surface cleaning: RFP (incumbent: Locus)
         "Disney seeking AMR vendors for hotel operations across 25+ properties" (2026-09-11)
         https://example.com/rfp
     ▸ Delivery / room service: RFP
         "RFP issued for autonomous delivery robots" (2026-09-15)
     Already has: Restroom / sanitizing (Xenex)
     Likely next: Security / patrol, Concierge / greeting
```

### Sales-Ready Format (DAILY_BUYERS_FORMAT=sales)
```
001  Disney Parks & Resorts
Entertainment & Hospitality · Orlando, FL
Job: Floor & surface cleaning; Delivery / room service
Robot Types: Floor cleaning robots; Delivery and serving robots
Schedule: High-intent window (est. 45–120 days) | Has Robots: Yes — Restroom / sanitizing | Budget: $60.0M
Status: RFP (incumbent: Locus)
"Disney seeking AMR vendors for hotel operations across 25+ properties" (2026-09-11)
"RFP issued for autonomous delivery robots" (2026-09-15)
Likely Next: Security / patrol, Concierge / greeting
```

**Key differences:**
- Sales format emphasizes **Job** and **Robot Types** over technical categories
- **Schedule** and **Budget** are surfaced prominently
- **Has Robots** indicator replaces "Already has" bullet
- Cleaner visual hierarchy for scanning
- Evidence quotes are not nested under categories

## Future Enhancements

Potential additions:
- HTML/PDF rendering with visual formatting
- Contact name extraction and inclusion
- Decision-maker role mapping
- ROI/savings calculations from evidence
- Confidence scores for extracted intelligence
- Multi-language support for international buyers
