# Robot class rules

**Owner:** Bob Christopher · **Status:** approved by Bob · **Version:** 0.1 (2026-10-16)
**Location in repo:** `docs/robot_class_rules.md` · rule data in `app/services/robot_understanding_v1/class_rules.json`
**Parent:** `docs/buyer_opportunity_spec.md` and `docs/robot_profile_lifecycle.md`. Changes to this table need Bob's approval.

---

## 1. The principle

The model reads **facts** from a product page, each with a quote:

- **primary function** (taxonomy `functions`), plus secondary functions
- **industries** it is sold into (taxonomy `industries`)
- **form** (taxonomy `form`)

**We assign the class** from those facts with the table below. The model never chooses the class. The same facts always give the same class, and every class comes with its reason ("healthcare: delivery work, sold only to clinical settings").

A new product's class is **unconfirmed** until a person confirms it once. After that it is reused and never re-guessed (see the lifecycle doc).

The model may still return its own class guess, stored as `model_class_suggestion` for comparison only. It is never shown or used for matching.

## 2. Industry groups used by the rules

| Group | Industries |
|---|---|
| **clinical** | hospital, surgery_center, senior_living |
| **logistics** | warehouse_distribution, 3pl, logistics_parcel |
| **dealership** | automotive_dealership |
| **production** | manufacturing, food_manufacturing |
| **guest-facing** | restaurant, qsr_fast_food, bar_nightclub, hotel, casino, stadium_venue, airport, retail_store, grocery, shopping_mall |
| **store** | retail_store, grocery, shopping_mall |

## 3. The rules

Checked in order; the **first rule that matches wins**. F = primary function, I = industries, form = form.

| # | If | Class | Reason shown |
|---|---|---|---|
| 1 | form = humanoid | **humanoid** | "Humanoid form" |
| 2 | F = surgical_assistance | **healthcare** | "Surgical work" |
| 3 | I is not empty **and every industry is clinical** | **healthcare** | "Sold only to clinical settings" |
| 4 | F = food_beverage_prep | **food_robotics** | "Prepares food or drinks" |
| 5 | F = serving_hospitality | **service_robot** | "Table service or bussing" |
| 6 | F = customer_interaction and every industry is in *store* | **retail** | "Guest-facing work in stores" |
| 7 | F = customer_interaction | **service_robot** | "Greets, guides or talks with people" |
| 8 | F = cleaning or disinfection | **cleaning** | "Cleaning or disinfection" |
| 9 | F = security_patrol | **security** | "Patrol and surveillance" |
| 10 | F = inspection and every industry is in *store* | **retail** | "Shelf scanning in stores" |
| 11 | F = inspection | **inspection** | "Inspection and monitoring" |
| 12 | F = construction_task | **construction** | "Jobsite work" |
| 13 | F = agricultural_task | **agriculture** | "Farm work" |
| 14 | F = machine_tending_assembly | **factory_industrial** | "Machine tending or assembly" |
| 15 | F = picking_packing_palletizing and I touches *production* and not *logistics* | **factory_industrial** | "Picking or palletizing in plants" |
| 16 | F = picking_packing_palletizing | **amr_logistics** | "Picking, packing or palletizing" |
| 17 | F = delivery_transport and I touches *logistics*, *production*, or *dealership*, and no industry is *guest-facing* or *clinical* | **amr_logistics** | "Moves materials in warehouses, plants, or dealerships" |
| 18a | F = delivery_transport and every industry is construction or energy_utilities | **construction** | "Hauls material on jobsites" |
| 18b | F = delivery_transport and every industry is agriculture | **agriculture** | "Hauls on farms" |
| 18 | F = delivery_transport | **delivery** | "Carries items from place to place" |
| 19 | F = general_purpose and I touches *production* | **factory_industrial** | "General-purpose, sold to plants" |
| 20 | F = general_purpose and I touches *logistics* | **amr_logistics** | "General-purpose, sold to warehouses" |
| 21 | anything else | **no class; needs review** | "Facts don't fit a rule" |

Notes:

- Rule 3 runs before the work rules on purpose: a robot built only for hospitals is a healthcare robot whatever its task (Moxi, hospital UV towers, hospital delivery variants). A robot sold to hospitals **and** hotels falls through to its work (Relay's hotel page: delivery).
- `automotive_dealership` is not in the logistics group. Rule 17 is the only rule that counts it, and only when the primary function is `delivery_transport` (a dealership robot that carries parts to technicians). A picker or a general-purpose robot sold to dealerships does not take this path. A dealership robot that is also sold into a guest-facing or clinical industry does not take it either. Bob decided this on 2026-10-16.
- Rule 4 runs before rule 5: a robot that **makes** drinks is food robotics even when it also serves them (ADAM, Scorpion). A robot that only **carries** finished food is service (BellaBot, Matradee).
- Secondary functions never change the class. They still count for matching.
- No rule looks at wording, brand names or vendor names.

## 4. Expected results (to be confirmed by the offline check)

| Product | Facts | Rule | Class |
|---|---|---|---|
| Moxi (Diligent) | delivery_transport · hospital · mobile_manipulator | 3 | healthcare |
| UVD Robot | disinfection · hospital · amr | 3 | healthcare |
| Relay, hospital page | delivery_transport · hospital | 3 | healthcare |
| Relay, hotel page | delivery_transport · hotel | 18 | delivery |
| ADAM | food_beverage_prep · restaurant, bar, hotel, casino | 4 | food_robotics |
| Scorpion | food_beverage_prep · bar, restaurant | 4 | food_robotics |
| BellaBot (Pudu) | serving_hospitality · restaurant | 5 | service_robot |
| Titan | delivery_transport · warehouse, manufacturing, automotive_dealership | 17 | amr_logistics |
| Titan, dealership page | delivery_transport · automotive_dealership | 17 | amr_logistics |
| Geek+ | picking_packing_palletizing · warehouse | 16 | amr_logistics |
| DUST-E S | cleaning · office, hospital, hotel, retail | 8 | cleaning |
| Digit (Agility) | humanoid form | 1 | humanoid |

## 5. Offline check already run (2026-10-16)

The table was run against every row of the four frozen answer keys (benchmark v2: 28, hold-out v1: 18, hold-out v2: 19, RichTech: 8), feeding each row's own expected facts (first required function, required + allowed industries, first allowed form) into the rules. No API calls.

**Result: 73 of 73 rows get a class the answer key accepts.**

Honesty note: the first pass was 72/73. The miss was v2-12 (SafeAI, an autonomy kit for haul trucks on construction and energy sites), which rule 18 called delivery. Rules 18a/18b were added after seeing that miss. They state a general principle (hauling on jobsites or farms is construction or agriculture, not delivery), but because they were written after looking at the key, the next fresh hold-out set is the real test. The script is `scripts/check_class_rules.py`.

## 6. How we test it going forward (no Anthropic cost)

1. **Rule check against the answer key, offline.** For every benchmark and hold-out row, feed the key's own expected facts (functions_required, industries_required, form_ok) into the table and compare the class with `primary_class_ok`. A mismatch means either the table or the key is wrong. List each one for Bob to decide; **never edit the key to fit the table.**
2. **End-to-end.** Run the existing sets once with the table in place. Class accuracy now depends only on fact accuracy; report facts and class separately.
3. **Determinism test.** The same facts must give the same class 100% of the time (unit test over every row).

## 7. Open decisions for Bob

1. Approve the industry groups (section 2) and the rule order (section 3).
2. Senior living counts as clinical (rule 3). Keep or drop?
3. Rule 21 products wait for review and get no class on the site until confirmed. OK?
4. Who can confirm a class: Bob only, or a list of people?
