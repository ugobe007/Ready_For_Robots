# Outcome — Simplify the Robot Job Card

**Date:** 2026-08-24  
**Mission:** `missions/2026-08-24-simplify-job-card`  
**Type:** build

## Diff

- Expanded Job Card shows slot + **3 model links** (OpenVLA / Isaac / HF weights). No survey, talent, or price URLs.
- Open questions capped at **3**. Qualify filters and pricing stay in ontology for a later step.
- Dropped the hardware essay, lookup notes, search-families, and “How we qualify / Where to find price” blocks.

## Tests

- vitest Job Card + workflow — 32 passed

## Follow-ups

Surface pricing lookups after the user takes a job forward (CRM / site assessment), not on the posting.
