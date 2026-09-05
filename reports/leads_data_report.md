# Leads & Scraper Data Report

**Generated:** 2026-03-18 (from live API: ready-2-robot.fly.dev)

---

## 1. Scraper status

| Metric | Value |
|--------|--------|
| **Target** | 100–200 leads/day |
| **Last 24h** | **293 companies**, 425 signals |
| **Status** | ✅ On track (195% of 150-lead target) |
| **Total DB** | 2,921 companies, 4,074 signals |

### Daily breakdown (last 7 days)

| Date | New companies | New signals |
|------|----------------|-------------|
| 2026-03-18 | 102 | 147 |
| 2026-03-17 | 396 | 545 |
| 2026-03-15 | 1,411 | 1,707 |
| 2026-03-14 | 125 | 162 |
| 2026-03-13 | 31 | 41 |
| 2026-03-12 | 80 | 95 |

*(No data for 2026-03-16 in the window — likely no discoveries that day.)*

---

## 2. What the leads are telling us [data]

### Pipeline summary (excl. junk)

| Tier | Count | % |
|------|-------|---|
| **HOT** | 104 | 3.6% |
| **WARM** | 62 | 2.1% |
| **COLD** | 2,753 | 94.3% |
| **Total** | 2,919 | 100% |
| Junk filtered | 2 | — |

- **Total signals across all leads:** 4,074

### By industry (where automation intent is showing up)

| Industry | Lead count | Note |
|----------|------------|------|
| Other / unclassified | 1,037 | Largest bucket; good target for reclassification |
| **Hospitality** | 708 | Strong segment (hotels, travel) |
| **Logistics** | 438 | Warehousing, fulfillment, distribution |
| **Healthcare** | 160 | Hospitals, care facilities |
| **Food Service** | 133 | Restaurants, QSR, catering |
| **Retail** | 99 | Stores, e‑commerce ops |
| **Medical Technology** | 71 | Devices, pharma-adjacent |
| **Datacenters** | 75 | Critical infrastructure |
| **Airports & Aviation** | 73 | Ground ops, cleaning, baggage |
| **Apparel & Textiles** | 46 | Manufacturing + distribution |
| **Casinos & Gaming** | 22 | Properties, F&B, facilities |
| **Food Processing & Manufacturing** | 21 | Processing plants |
| **Theme Parks & Entertainment** | 14 | Parks, venues |
| **Airports & Transportation** | 9 | Ground transport |
| **Cruise Lines** | 7 | Ships, hospitality |
| **Real Estate & Facilities** | 6 | FM, cleaning, security |

**Takeaway:** Hospitality and logistics dominate; healthcare, food service, retail, and airports are strong secondary segments. “Other” is the biggest slice — reclassifying those (e.g. via `/api/leads/reclassify-unknown`) will sharpen the picture.

---

## 3. Sample HOT leads (what “high intent” looks like)

| Company | Industry | Signals | Why HOT |
|---------|----------|---------|---------|
| ABM Industries | Real Estate & Facilities | 9 | 4 intent signals (strategic_hire, capex) |
| Co-op | Logistics | 13 | High-fit industry + many signals |
| Capital | Food Service | 7 | MA + funding_round + industry fit |
| DB Schenker | Logistics | 4 | Capex, strategic_hire |
| Dollar General | Logistics | 5 | Capex, strategic_hire |
| Five Below | Logistics | 4 | Capex, strategic_hire |
| Aimbridge Hospitality | Hospitality | 5 | Capex, strategic_hire |
| Travelodge UK | Hospitality | 3 | Capex |
| Albertsons | Logistics | 4 | Capex, strategic_hire |
| Mitie | Airports & Aviation | 18 | Funding, MA, many signals |
| Brightspring Health | Healthcare | 4 | MA, strategic_hire |
| Wynn Resorts | Casinos & Gaming | 4 | Capex, strategic_hire, enterprise |

**Signals driving HOT:** `strategic_hire`, `capex`, `funding_round`, `ma_activity`, plus high-fit industries (logistics, hospitality, healthcare, food service).

---

## 4. Sample WARM leads

- **Fetch Robotics**, **CMES Robotics**, **Boulanger**, **Equipment** (and similar) — mostly **Logistics**, score ~73–74. Expansion, job postings, labor shortage, and news signals typical for WARM.

---

## 5. Summary: what the data says

1. **Scraper is healthy** — 293 new companies in last 24h, above target; big spike on 2026-03-15 (1,411 companies) shows capacity for large discovery runs.
2. **Intent is concentrated** — 104 HOT + 62 WARM = 166 high-value leads; rest are COLD but still in pipeline for future scoring/signals.
3. **Verticals to prioritize:** Hospitality (708), Logistics (438), Healthcare (160), Food Service (133), Retail (99). Airports, datacenters, and casinos are smaller but present.
4. **“Other” is the main blind spot** — 1,037 leads; running industry reclassification will improve segmentation and messaging.
5. **HOT pattern:** Capex + strategic hires (and often funding/MA) in logistics, hospitality, healthcare, and food service. Good for targeting “ready to buy” narratives.

---

*End of report. Data from `GET /api/scraper/stats/daily?days=7`, `GET /api/leads/summary`, `GET /api/scraper/status`, and `GET /api/leads?tier=HOT|WARM`.*
