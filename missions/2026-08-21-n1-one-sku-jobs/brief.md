# Fourier N1: one picker confirm → jobs + Activate

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface  
**ICP:** OEM submits a lineup URL, then picks **one** SKU (`https://www.fftai.com/en` → N1)

## Goal

Picking one robot from the lineup is the Find-jobs decision. Land on **Jobs for that product** with **Activate job list** visible. Do not ask Find jobs a second time. Do not leave step 2 as a dead end.

## Why

Live Fourier path: step 1 recognizes products → choose N1 → asked to look for jobs twice (picker CTA, then profile checkpoint). Jobs for N1 then appear with **no next step** (Activate buried below the fold / process nav easy to miss). Same break as empty portfolio: the trail stops at 02.

## Acceptance

1. One selected SKU (`names.length === 1`) goes to job search, then jobs — not `enterReview`.
2. Heading for one robot is `Jobs for Fourier N1`, even when the match is type-first.
3. Jobs stage pins **Activate job list →** (not only after scrolling the cards).
4. Process nav 03 is a real link once jobs are on screen.
5. Vitest for workflow + workspace contract green.

## Out of scope

- Matcher retune / SIGNAL / Qualify
- Changing the picker
- Seeding extra Fourier SKUs
