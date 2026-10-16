# RFR Spec Addendum: Robot Profile Lifecycle

**Owner:** Bob Christopher · **Status:** draft for Bob's approval · **Version:** 0.2 (2026-10-15: robot job wording; two classifications meet at the workflow)
**Location in repo:** `docs/robot_profile_lifecycle.md`
**Parent:** `docs/buyer_opportunity_spec.md` (v1.6). This addendum extends it; where they disagree, the parent spec wins until Bob approves a change. Schema changes below are **proposals**: none may be built without Bob's explicit approval and a confirmed backup.

---

## 0. The logic in one paragraph

A robot seller gives us a URL. We find the robots on that site, profile each one once, and keep the profile current when the product page changes. Each profile is matched to **buyers** (companies that buy or rent robots), and each buyer shows its **robot jobs** where that robot fits: one per workflow (company × workflow × readiness signals), with the evidence that the buyer is moving now. A seller with several robots switches between their profiles to see each robot's buyers. We record what sellers do with those matches, and use the outcomes to rank future matches better.

In code: buyer = `rfr_buyers`, robot job = `rfr_opportunities` (buyer × workflow), robot profile = this document's `rfr_robot_profiles`.

**Two classifications meet at the workflow.** Robots are classified from product pages (taxonomy: form, class, functions, industries). Buyer intent is classified from what companies publish (parent spec §5, §5a: signal type, workflow, intent strength). No phrase, however it is worded ("automate labor", "physical AI deployment", "robot PoC", "replace manual processes"), is ever a match key. A phrase is evidence; the classified **workflow** is what joins a robot to a buyer. **No workflow, no robot job.** A phrase saying the buyer has already deployed robots in a workflow closes that workflow (`committed`); it never opens one.

---

## 1. The loop

```
URL ──► 1 Discover ──► 2 Identify ──► 3 Classify ──► 4 Profile (save)
                                                        │
             5 Watch for page changes ◄─────────────────┤
                                                        ▼
        9 Learn ◄── 8 Record ◄── 7 Choose robot ◄── 6 Match to buyers
         │                                              ▲
         └──────────── better ranking ──────────────────┘
```

| # | Stage | Status 2026-10-15 | Where |
|---|---|---|---|
| 1 | Discover robots on the site | Partly built; homepage bug #340 | `phase2_match.discover_product_pages`, `vendor_robot_lookup` |
| 2 | Identify each robot by name | Built | `pick_product_record`, `url_names_product` |
| 3 | Classify capabilities | Built; AI-capability field missing (§3) | `taxonomy_extraction.py`, `taxonomy.v1.json` |
| 4 | Save the profile, reuse it | Built per URL (#334); no per-robot profile yet (§4) | `rfr_robot_products`, `saved_clean_product` |
| 5 | Detect page changes, update | Not built | §5 |
| 6 | Match profile → buyers → opportunities | Logic built; runs on sample data until buyers are seeded | `phase2_match`, spec §7 |
| 7 | Seller picks among their robots | Picker built; "My robots" not built | `EditorialResults`, My desk design |
| 8 | Record actions, matches, correspondence | Scattered (old CRM, visit tracking) | §8 |
| 9 | Learn from outcomes | Not built | §9 |

---

## 2. Discover and identify (stages 1–2)

1. **Product URL** (has a product slug): classify that page; keep only the record the URL names. Never substitute a sibling.
2. **Maker homepage** (no slug): list the maker's robots (links on the page, then the vendor catalog) and show the picker. A homepage **never** collapses into one robot, unless the maker sells exactly one robot (e.g. relayrobotics.com). Fix in #340.
3. **Same robot, several URLs** (`/adam`, `/solutions/adam`, a regional page): one profile (§4), several source URLs.
4. A page that isn't selling a robot (software, parts, integrator services, news) returns "not recognized". No guess.

## 3. Classify (stage 3)

Unchanged from the parent spec: taxonomy values only, each with a quote from the page, unsupported facts dropped.

**Gap: AI and foundation-model capabilities.** Today's taxonomy has no field for what a robot's intelligence can do. Sellers and buyers care (e.g. "learns new tasks from demonstration", "voice conversation with guests"). **Proposal for Bob** (taxonomy change, needs approval):

- New optional field `ai_capabilities`: a list, closed values, each with page evidence. Candidate values, to be confirmed by Bob before use:
  `autonomous_navigation`, `object_recognition`, `manipulation_learning` (learns tasks from demonstration or teleoperation), `natural_language_interaction` (voice or chat with people), `fleet_coordination`, `foundation_model_onboard` (the page names a vision-language-action or similar general model), `remote_teleoperation`.
- Used for **display and ranking** only at first, not as a hard match filter.
- Adding it bumps `taxonomy_version`, which invalidates saved profiles (§4) so they re-classify once.

## 4. Profile (stage 4)

**Today:** one `rfr_robot_products` row per URL × prompt version × taxonomy version, reused on repeat searches (#334). A repeat search costs no Anthropic call.

**Proposal for Bob** (schema change, needs approval and a backup):

`rfr_robot_profiles`: one row per robot product.

| Column | Meaning |
|---|---|
| `id` | |
| `maker_name`, `maker_domain` | e.g. Richtech Robotics, richtechrobotics.com |
| `product_name`, `product_name_normalized` | ADAM / adam |
| `current_version_id` | → the `rfr_robot_products` row in use |
| `status` | `active`, `discontinued` (page gone), `needs_review` |
| `created_at`, `updated_at` | |

Add to `rfr_robot_products` (each row becomes a **version** of a profile): `profile_id`, `content_hash` (hash of the page text that was classified), `superseded_at`.

Rules: versions are **appended, never overwritten or deleted**. The profile points to the newest clean version. A version with a worse classification (fewer fields) than the current one is kept but not promoted; it goes to `needs_review`.

## 5. Watch for changes (stage 5)

`rfr_page_watch`: one row per source URL: `url`, `profile_id`, `last_hash`, `last_checked_at`, `next_check_at`, `last_status` (ok, changed, gone, blocked).

1. A scheduled job (worker, **never the web machine**: see #335) re-fetches each watched URL. Default every 14 days; robots in a seller's "My robots" every 7.
2. Same page-text hash → update `last_checked_at`, no Anthropic call.
3. Different hash → classify again → new version (§4). If the classification changed (new industry, new function, new form), note it on the profile and in the seller's **Alerts**: "ADAM now lists hotels and casinos."
4. Page gone (404 three checks in a row) → profile `discontinued`; matches stay, marked.
5. Budget: a daily cap on re-classifications (config), and `RFR_ALLOW_PAID_LLM` respected.

## 6. Match (stage 6)

Unchanged from the parent spec §7: profile industries and functions joined to buyers' workflows; form must fit the work; committed workflows excluded; ranked by signal tier and age. Each **buyer** shows its **robot jobs** (one per workflow) with the evidence.

Today this runs against the example set. It becomes real when `rfr_buyers`, `rfr_workflows` and `rfr_signals` have rows: the seed buyer list (Bob) and the SAM.gov feed (Phase 3). **This is the biggest gap in the loop.**

## 7. Choose among robots (stage 7)

- Maker homepage → picker → one or more robots → results per robot.
- Signed in: **My desk → My robots** lists the seller's saved profiles; picking one shows its buyers. A buyer can appear under several robots; the buyer page lists every robot of theirs that fits.
- Saving a robot adds its URL to the watch list (§5).

## 8. Record (stage 8)

**Proposal for Bob** (schema change): `rfr_events`, an append-only activity log.

| Column | Meaning |
|---|---|
| `id`, `occurred_at` | |
| `account_id` | the seller (null for signed-out visitors; a session id instead) |
| `event_type` | closed list below |
| `profile_id`, `buyer_id`, `workflow`, `opportunity_id` | whichever apply |
| `detail` | small JSON (e.g. filter used, stage from → to) |

Event types: `search_submitted`, `robot_picked`, `results_shown`, `buyer_opened`, `source_opened`, `buyer_saved`, `stage_changed` (Saved → Contacted → Meeting → Site assessment → Pilot → Won / Lost), `buyer_dismissed` (with reason: wrong industry, already automated, too small, other), `hubspot_synced`, `alert_opened`.

**Correspondence:** record only that an email was sent or received and its stage effect, not message bodies, unless the seller turns on inbox sync with clear consent. No auto-sending.

## 9. Learn (stage 9)

1. **Labels come from outcomes:** a buyer the seller moved to Meeting, Pilot or Won is a positive for that robot class × workflow × industry × signal type. Dismissed with a reason is a negative.
2. **What learning may change:** ranking weights (signal tier weights, decay, industry and workflow priors), and which industries to add next.
3. **What learning may never change:** the taxonomy, the classifier's answer key and scorer (frozen), the form-fit rule, or anything that would show a seller a buyer that is already committed in that workflow.
4. **How:** a weekly offline report first (which signals led to meetings, by robot class and industry). Weight changes go in a draft PR with before/after on held-out outcomes; Bob approves. No automatic re-weighting in production for v1.
5. Minimum data before any weight change: 30 positive outcomes in the segment.

---

## 10. Build order (one draft PR each)

1. #340: homepage never collapses into one robot.
2. Seed buyers (Bob's list) → `rfr_buyers`, `rfr_workflows`. *(parent spec, needs the list)*
3. SAM.gov → `rfr_signals` (parent spec Phase 3).
4. Results read real opportunities when they exist; Example cards only fill gaps.
5. **Approval gate:** Bob approves §4 and §8 schema, with backup confirmed.
6. Profiles and versions (§4), backfilled from existing `rfr_robot_products` rows (insert only).
7. Page watch (§5) on a worker, with Alerts.
8. Event log (§8) wired to results, buyer page, My desk.
9. My robots tab (§7).
10. Outcome report (§9.4). Ranking changes only after 30+ positives per segment.
11. `ai_capabilities` (§3), after Bob confirms the value list.

## 11. Open decisions for Bob

1. Approve `rfr_robot_profiles`, versions on `rfr_robot_products`, `rfr_page_watch`, `rfr_events` (§4, §5, §8).
2. Confirm the `ai_capabilities` values (§3), or replace them.
3. Re-check interval (14 days default, 7 for saved robots) and daily re-classify cap.
4. Whether to store email bodies with consent, or never (§8).
5. Dismiss reasons list (§8).
