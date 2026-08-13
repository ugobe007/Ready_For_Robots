# Mission: conversion-cal-curiosity

**Date:** 2026-08-13  
**Agent:** ProductSurface + Cal  
**Type:** build

## Goal

Fix ReadyForRobots’ biggest weakness — visitor → user conversion — by making Cal sound like a curious, informed peer (not a robotic pitch), then proving that voice on anonymous `/pipeline` and chasing Hermes digest winners.

## Conversion hypothesis

If OEMs see a short, timely Cal note that sparks “huh, that’s interesting” instead of a consultant sermon, they will signup to save/copy — and buyers will reply instead of bounce.

## Primary metric

Signup starts from `/pipeline` (funnel). Qualitative: golden drafts for PFG/Medline feel timely. Secondary: outbound reply tone after regenerate.

## Acceptance

- Buyer variants ≤ ~150 words; no Robert/RFQ first-touch close; pass Cal voice tests
- Curiosity framing on AnonymousValueStrip + Outreach panel + Home
- Digest winners prioritized; drafts regenerated after Fly deploy
- `CAL_INCLUDE_BUYING_WINDOW` remains off
- Fly + Vercel deployed; samples in `outcome.md`

## Out of scope

Buying-window flag flip; Stripe; new auth providers.
