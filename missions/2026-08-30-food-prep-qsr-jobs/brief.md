# Food prep / QSR FIND class (not hotel hospitality)

**Date:** 2026-08-30
**Type:** build
**Agents:** ProductSurface + ontology + ScraperOps
**Status:** in progress

## Goal

Chipotle and QSR operators want **food prep** robots. FIND **Hospitality** aliased `food_prep` onto hotel guest service (Hilton / Hyatt / Four Seasons). Split **Food prep** into its own FIND class, ontology work language, tile, and job-board scrape targets. Do not invent a Chipotle Job Card.

## Acceptance

1. Production FIND hospitality / food_prep currently shows hotel cards — confirm QSR absence.
2. Ontology: distinctive QSR words map to `food_prep`, not hotel housekeeping.
3. FIND tile **Food prep**. `lookup_grain=robot_type` + `food_prep` → Job Cards or honest empty copy.
4. Scrapers: kitchen / QSR operational URLs (not VP of Culinary). Overlay named employers.
5. Honest gap if Chipotle itself has no live posting. Diligent stays healthcare.

## Out of scope

SIGNAL hop. Invented emails. Fake Chipotle employer. Fly in apiBase.ts.
