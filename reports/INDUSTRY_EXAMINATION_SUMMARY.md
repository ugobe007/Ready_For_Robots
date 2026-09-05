# Examination of "Other" (Unknown Industry) Leads

**Date:** 2026-03-19  
**Source:** API sample (384 leads with industry=Other from 1,476 fetched)

---

## What these leads actually are

1. **Real companies we can now classify**
   - **Automotive & manufacturing:** Hyundai Motor Group, Hyundai Motor, BMW Group, STMicroelectronics, Teradyne Robotics, Rockwell Automation, OMRON, Viega North America
   - **Medical / surgical:** Vitestro (phlebotomy), VSee (telehealth), Roen Surgical, Surgerii Robotics, Brain Corp
   - **Airlines / transit:** Hawaiian Airlines, Metro (LAX)
   - **Theme parks / recreation:** Six Flags, Stevens Pass (ski)
   - **Food / beverage:** LifeSpire (senior living overlaps healthcare), “Food and Beverage Industry” projects

2. **Noise / false positives (publishers or headline fragments)**
   - “System”, “Elon Musk”, “Expanded”, “EV rivals”, “Best Robot Vacuums”, “Manufacturing Dive.”, “Jerusalem Post.”, “Times”, “Goldman Sachs”, “Nikon”, “Billion Spending”, “Beloved burger chain”, “Global M&A”, “Investment Backdrop Heading”
   - These are often article titles or publisher names extracted as “companies”. Classifying them as **Media & Publishing** makes it easier to filter or deprioritize.

3. **Keyword signal (after stripping HTML)**
   - Strong: **2026**, **robotics**, **humanoid**, **hyundai**, **manufacturing**, **motor**, **group**, **industrial**, **automated**, **autonomous**, **deploy**, **surgical**, **stocks**, **market**, **report**
   - Bigrams: **hyundai motor**, **motor group**, **humanoid robots**, **ces 2026**, **to deploy**

---

## Changes made to the industry list

**File:** `app/services/industry_inference.py`

### New industries

| Industry | Purpose |
|----------|--------|
| **Automotive & Manufacturing** | Factory, assembly, semiconductor, cobots, humanoid deployment; Hyundai, BMW, Teradyne, Rockwell, OMRON, STMicroelectronics |
| **Media & Publishing** | Publishers and headline fragments (e.g. Manufacturing Dive, Motley Fool, NYT) so they can be filtered or deprioritized |

### Expanded keywords on existing industries

| Industry | Additions |
|----------|-----------|
| **Airports & Aviation** | airlines, airline, metro, transit, transportation, lax station |
| **Medical Technology** | telehealth, phlebotomy, surgical, surgery robot, vitestro, roen surgical, surgerii |
| **Theme Parks & Entertainment** | six flags, ski resort, stevens pass |

---

## Next steps

1. **Re-run reclassify**  
   Call `POST /api/leads/reclassify-unknown` again (after deploy) so the new keywords and industries are applied. More of the 1,033 unknown leads should move into Automotive & Manufacturing, Medical Technology, Airports & Aviation, Theme Parks & Entertainment, and Media & Publishing.

2. **Optional: junk rules**  
   Consider marking or filtering “companies” that are really publishers (e.g. industry = Media & Publishing and signal_count &lt; 2) so they don’t clutter HOT/WARM lists.

3. **Re-examine after reclassify**  
   Run `scripts/examine_other_leads_via_api.py` again and review `reports/unknown_industry_leads_sample.txt` and `reports/unknown_industry_keyword_analysis.txt` to see what remains in Other and whether to add more industries or keywords.

---

## Report files

| File | Contents |
|------|----------|
| `reports/unknown_industry_leads_sample.txt` | Up to 350 “Other” leads with company name, signal count, and first 400 chars of combined text |
| `reports/unknown_industry_keyword_analysis.txt` | Top 120 words and top 80 bigrams (for adding more keywords later) |
