# Buyer Opportunities — Phase 0 baseline

Spec: `docs/buyer_opportunity_spec.md` §10, Phase 0. No code changed.

What the live site did on 2026-10-14 (15:35–15:45 UTC) for 3 robot URLs, end to end. Site `https://readyforrobots.com` (bundle `index-DJra3M2u.js`, not the stale build), API `https://ready-2-robot.fly.dev`. Raw API responses and page text are in `docs/buyer_opportunity_phase0/`.

The 3 URLs are from the spec's suggested acceptance robots (§11), one per top pilot group:

| Robot URL | Pilot group |
|---|---|
| `https://locusrobotics.com` | 1 Warehouse, logistics, 3PL |
| `https://www.richtechrobotics.com` | 3 Hotels and casinos (+ 6 Restaurants) |
| `https://relayrobotics.com` | 4 Hospitals |

## How it was run

- **API:** `POST /api/robot-job-search` with the same body the FIND page sends (`url`, `product`, `max_sources: 6`, `asserted_class`, `lookup_grain`). First the URL alone, then the choice a user makes next: a product, or a robot class.
- **UI:** headless Chromium on `https://readyforrobots.com/`. Paste the URL, press Enter, click the product or class, then save a screenshot and the visible text. The network log records the request bodies the page sent.
- **Side effects:** each search updates that URL's row in the robot submissions table (ids 23, 12 and 1 already existed) and sends `/api/track/visit` calls. No signup, no CRM writes.

## Robot 1: Locus Robotics

**Step 1, URL only:** `state=select_product` in 0.8 s, 0 jobs.
- The 4 products (Locus Origin, Vector, Max, Flex) come from the vendor robot index, not from reading the page ("Picker lists vendor index SKUs only").

**Step 2, product Locus Origin:**
- `state=matches`, `robot_class=warehouse`, `matcher=requirement_v1`.
- `job_count=25`, 12 returned.
- Capabilities: mobile platform, tote/warehouse transport, item transport.

| # | Employer | Location | Industry on card | Job |
|---|---|---|---|---|
| 1 | CuraScript SD | Tempe, AZ | specialty pharma dc | Return empty totes from packing to operating area |
| 2 | Intuitive Surgical | United States (med-device mfg) | Aerospace | Move aircraft production kits |
| 3 | Skyline Airport Services | Denver, CO | Airport | Deliver supplies and amenities between gates and lounges |
| 4 | Hilton Worldwide | McLean, VA | Hotel | Deliver guest luggage to hotel rooms |
| 5 | CuraScript SD | Tempe, AZ | Specialty pharma | Return empty pharma totes |
| 6 | Intuitive Surgical | United States (med-device mfg) | Med device | Move system carts |
| 7 | Mercy General Hospital | Columbus, OH | Healthcare | Deliver medication carts |
| 8 | Lakeside Regional Hospital | Kenosha, WI | Hospital | Move supply carts |
| 9 | Intuitive Surgical | United States (med-device mfg) | Med device | Replenish point-of-use |
| 10 | Intuitive Surgical | United States (med-device mfg) | Aerospace | Deliver kits to line |
| 11 | NAPA Auto Parts | Duncansville, PA | Auto parts DC | Move completed orders |
| 12 | Intuitive Surgical | United States (med-device mfg) | med device manufacturing | Point-of-use replenishment and packing-system cart/kit movement |

- **Industries:** 3 of 12 are warehouse/distribution work (CuraScript ×2, NAPA). The rest are a surgical-robot maker (×5, two of them tagged Aerospace), an airport, a hotel and hospitals.
- **Intuitive Surgical:** it makes robots, which makes it supply, yet it appears as an employer 5 times.
- **UI** (`ui_locus_text.txt`, `ui_locus_2_after_choice.png`):
  - The header says "3 EXAMPLE JOBS" while the text says "25 example jobs".
  - 3 cards are shown, then "Unlock 9+ More Job Opportunities … Upgrade your workspace".
  - Cards 3 and 4 in the list are the same Hilton job twice.

## Robot 2: Richtech Robotics

**Step 1, URL only:** `state=select_product`, 0 jobs. 11 products from the vendor index: ADAM, MATRADEE, MATRADEE X, MATRADEE L, LUCKI, MEDBOT, DUST-E MX, AIDY, Scorpion, Titan, Scotty.

**Step 2a, ADAM:** `state=matches`, `robot_class=serving`, 3 jobs.
- Capabilities listed: mobile platform, beverage preparation, table/drink/bussing service.
- The vendor index describes ADAM as "Beverage and cocktail preparation. Restaurants · bars."

| # | Employer | Location | Job |
|---|---|---|---|
| 1 | Darden Restaurants | Orlando, FL | Bus tables and return dishware to the kitchen |
| 2 | Marriott International | Bethesda, MD | Run room-service orders to guest rooms |
| 3 | The Cheesecake Factory | Calabasas, CA | Run food and drinks to dining tables |

- None of the 3 is drink preparation. All 3 need a mobile robot.
- No casino appears.

**Step 2b, MATRADEE (delivery):**
- `job_count=25`, `robot_class=null`.
- The 12 returned cards are **identical** to Locus Origin's list: pharma totes, aircraft kits, hospital carts.
- No restaurant, hotel-dining or casino card.

**UI for ADAM** (`ui_richtech_text.txt`): the same 3 cards. The expanded card shows "Employer / Workplace / Work" and "Potential contract value $5,000–$7,500 / month".

## Robot 3: Relay Robotics

**Step 1, URL only:** `state=qualify_robot`, 0 jobs.
- One product from the vendor index: "Relay: hotel delivery. Used in Hospitality."
- The live page was not fetched ("Catalog vendor — skipped live manufacturer fetch").
- The user must pick 1 of 20 robot classes.

**On the site, choosing Healthcare** (`ui_relay_network.json`, `ui_relay_healthcare_click.png`):
- The page sends `{"product":"Relay","asserted_class":"healthcare","lookup_grain":"product"}`.
- The API answers `state=thin_corpus`, `zero_reason=insufficient_profile_evidence`, 0 jobs.
- The page then says: "No healthcare jobs for this robot yet … This is a coverage gap on our side, not a limitation of the robot." The API's own reason was missing profile evidence, not missing jobs.

**The same class through the API without `product`/`lookup_grain`:** `state=matches`, 11 jobs. So the result for the same robot and class depends on a hidden request field.

| # | Employer | Location | Industry | Job |
|---|---|---|---|---|
| 1 | Lakeside Regional Hospital | Kenosha, WI | Hospital | Deliver meal trays and linens to patient floors |
| 2 | Mercy General Hospital | Columbus, OH | Hospital | Deliver medications from pharmacy to patient units |
| 3 | Summit Health Medical Center | Reno, NV | Hospital | Deliver medications and IV supplies to nursing floors |
| 4 | Parkland Health | Dallas, TX | Hospital | Run nursing-unit errands and supply fetches |
| 5 | UCSF Health | San Francisco, CA | Hospital | Restock unit-dose medications from central pharmacy |
| 6 | Riverside Health System | Newport News, VA | Hospital | Transport lab specimens to the laboratory |
| 7 | St. Anne Medical Center | Toledo, OH | Hospital | Replenish supply carts to nursing units |
| 8 | Maple Grove Assisted Living | Rochester, MN | Assisted living | Deliver linens and amenities to resident rooms |
| 9 | Brookhaven Senior Living | Naperville, IL | Senior living | Deliver meals to resident rooms |
| 10 | Willow Bend Memory Care | Frisco, TX | Memory care | Deliver meals and snacks to memory-care residents |
| 11 | Cedar Ridge Care Center | Boise, ID | Skilled nursing | Move medication and supply carts between care wings |

**Hospitality class (API):** 3 jobs: Four Seasons (luggage), Hilton (amenities), Hyatt (room service).

## What every result has in common

1. **The cards come from a file bundled with the code, not from buyers.**
   - The match code reads `app/data/robot_job_match_corpus.json`: 134 entries, 99 employers.
   - Each entry's `source` label: `tier_seed` 53, `tape` 32, `hospitality_seed` 13, `demo` 10, `manipulation_ledger` 10, `healthcare_seed` 9, `vertical_seed` 7.
   - **No entry has a source URL.** No card links to any evidence that the company wants this work done.
   - I did not find this path reading `companies`, `signals`, `robot_jobs` or `deployment_events`. I traced the two data-file paths in `robot_requirement_match.py`, not every branch.
2. **Many employer names can't be tied to any source.** The file gives no source for Lakeside Regional Hospital, Mercy General Hospital, Summit Health Medical Center, Skyline Airport Services, Maple Grove Assisted Living, Willow Bend Memory Care, Cedar Ridge Care Center and others. I can't tell from the repo whether they are real.
3. **Invented contact data.**
   - Every card in the API response has `employer_email = operations@<company name with spaces removed>.com`, e.g. `operations@st.annemedicalcenter.com`. It is generated in `app/services/robot_job_capability_match.py`.
   - The same code and the corpus file also hold hard-coded decision-maker names (e.g. "Dr. Arthur Pendelton" for Intuitive Surgical, "Jim Callahan" for NAPA).
   - The Jobs page doesn't appear to display the email, but the public API returns it.
4. **Numbers the browser makes up.** These are not data:
   - Posted date, deadline, "N Spots Open", "3/3 Applicant Spots Filled · Proposals Under Review" and "FRESH MATCH / AGING" all come from a hash of the job key (`client/src/lib/jobLifecycle.ts`).
   - These are hard-coded for every card (`client/src/components/RobotJobsWorkspace.tsx`):
     - "Time frame 30–90 days — Active buying window extracted from signals";
     - "Public budget: $60,000–$90,000/yr";
     - "Decision owner: Operations Director (Plant Automation Owner)";
     - `verdict: "VERIFIED_BUYER"`, `signalType: "HOT BUYER"`, `score: 95`.
5. **No "why now".** No card has an RFP, pilot, budget, expansion or hiring signal, a date, or a source link. Every card's verdict is `POSSIBLE_MATCH`.
6. **No workflow status.** Nothing marks a workflow as already committed to robots, so nothing is excluded for that reason.
7. **Robot side.**
   - Product lists come from a vendor index, and catalog vendors skip reading the live page.
   - The taxonomy extractor (prompt v4) is not on this path. Classes like `serving` and `warehouse` come from the existing classifier.
8. **Signup and payment asks right after the first cards:**
   - "Unlock 9+ More Job Opportunities … Upgrade";
   - "Build a product presentation … Sign up and pay to order".
9. **Home page claims** (`ui_00_home_text.txt`): "3,000+ Verified Job Leads", "109+ Benchmarked Humanoids", and a "Verified physical work feed — 0066 jobs found". The feed lists the same kind of seed employers (Lakeside Regional Hospital, The Cheesecake Factory, NAPA, FreshCart E-Grocery, ExpressPost Hub). I did not trace where "3,000+" comes from.

## Compared with the spec

| Spec | Today |
|---|---|
| Buyer = real company with industries and workflows (§4.2–4.4) | Employers come from a bundled file with no sources |
| Why now: dated, sourced signals ranked by tier (§5–6) | No signals; timing and budget are hard-coded text |
| Committed workflows excluded (§6) | No workflow status |
| Robot makers never shown as buyers (§1, §7) | Intuitive Surgical is a buyer 5 times for Locus |
| Robot classified by the taxonomy extractor (§4.1, Phase 2) | Vendor index + existing classifier |
| No contacts or upgrade prompts on cards (§8, §12) | Generated `operations@` emails in the API; upgrade wall after 3 cards |

## Evidence files (`docs/buyer_opportunity_phase0/`)

- `doctor.json`: site and API health at the time of the run.
- `search_{locus,richtech,relay}.json`: step 1 (URL only).
- `step2_locus_origin.json`, `step2_richtech_adam.json`, `step2_richtech_matradee.json`, `step2_relay_healthcare.json`, `step2_relay_hospitality.json`: step 2 through the API.
- `ui_{locus,richtech,relay}_text.txt`, `ui_00_home_text.txt`: visible page text and the API calls the page made.
- `ui_relay_network.json`: the exact request bodies and results the page got for Relay.

Screenshots are attached to the PR, not committed.
