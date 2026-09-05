# Outcome — Food prep / QSR FIND class

**Date:** 2026-08-30
**Mission:** `missions/2026-08-30-food-prep-qsr-jobs`

## Answer

We were matching **hotel hospitality**, not QSR food prep.

Production `POST /api/robot-job-search` with `lookup_grain=robot_type` + `hospitality` **or** `food_prep` both returned Hilton / Hyatt / Four Seasons guest-service cards plus live hotel housekeepers. Zero Chipotle, zero make-line, zero bowl assembly. Live overlay is warehouse/mining/factory plus hotel housekeeping — not kitchen prep.

`food_prep` was an alias of Hospitality. Seed Job Cards for that tile were hotel guest service.

## After

- **Food prep** is its own FIND tile (`lookup_grain=robot_type` + `food_prep`).
- Hospitality stays hotel guest delivery / housekeeping. Chipotle-style QSR copy classifies as `food_prep`, not hotel. Diligent/Moxi stays healthcare.
- Ontology QSR words: make line, bowl assembly, grill, prep cook, QSR, fast casual, kitchen automation, ingredient dosing, tortilla, assembly line kitchen. pstack critic fails if they vanish.
- Scrapers: Food Service job-board URLs for make-line / bowl assembly / kitchen automation operational roles (not VP of Culinary). Overlay maps `food_prep` work language to the food_prep tape.

## Honest gap

Chipotle itself has **no live job-board posting** in production overlay. The food_prep matcher can still show existing corpus seeds (White Castle fry station, Shake Shack grill, Chipotle bowl assembly, Compass warewash) — those were already in `robot_job_match_corpus.json` as `hospitality_seed`, not invented this cycle. Empty copy if the corpus is empty: `No food prep jobs for this robot yet.` Next 6h Food Service scrape can persist named QSR employers from real postings.

## Tests

- pytest: ontology, food_prep class, industry tiles, healthcare/Diligent, job-board URLs, live overlay (128 + 34 related)
- vitest: class options, jobsWorkflow, pstackRelease (44)
- `python3 scripts/pstack_release.py --local` critic OK
