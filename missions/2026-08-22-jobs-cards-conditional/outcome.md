# Outcome — Job Cards stay Conditional

**Date:** 2026-08-22  
**Mission:** `missions/2026-08-22-jobs-cards-conditional`  
**Type:** build

## Diff

- Matcher `POSSIBLE_MATCH` / `INSUFFICIENT` render **Conditional**, not Qualified.
- Qualified is reserved for user or employer confirmation. Blockers still map to Not qualified.
- Expanded card states the hint (“Pending your review and a site assessment”) and lists matcher why as “Why this is listed.”

## Metrics

Not a pipeline-cache mission. FIND → cards → Next → CRM is the battle-test.

## Follow-ups

Do not retune M2 to fake qualification. Site assessment / employer feedback is later.
