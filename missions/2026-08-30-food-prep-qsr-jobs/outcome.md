# Outcome — Food prep / Serving / Cleaning FIND classes

**Date:** 2026-08-30
**Mission:** `missions/2026-08-30-food-prep-qsr-jobs`
**Branch:** `cursor/food-prep-qsr-jobs-009b`

## Answer

Food prep is **not QSR-only**. Hotel / casino / airport kitchens and QSR make-line are the same FIND class. Serving and Cleaning are their own tiles. Diligent stays healthcare.

## After (operator correction)

- **Food prep** — hotel / casino / airport kitchens **and** QSR make-line / grill / prep. Not hotel housekeeping.
- **Serving** — table / drink / bussing (ADAM, Matradee, Servi) in restaurants, hotels, casinos, airports, offices, malls. Not QSR-only, not housekeeping.
- **Cleaning** — floor / vacuum / restroom at hotels, restaurants, casinos, airports, offices, malls, **data centers**. Not hospital EVS.
- Hospitality stays guest delivery / housekeeping.
- Ontology + Indeed scrape URLs for those venues. No invented employers. No SIGNAL hop. Sibling scraper owns Fly pipeline cache.

## Honest gap

Live overlay only persists named postings. Empty copy if the corpus has no kitchen / serving / janitor rows yet: `No food prep|serving|cleaning jobs for this robot yet.`

## Tests

Targeted pytest + vitest + `python3 scripts/pstack_release.py --local`. No Fly pipeline cache refresh.
