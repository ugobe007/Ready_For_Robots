# Mission: Humanoid pilot ranking

**Date:** 2026-06-23
**Agent:** LeadQuality + ProductSurface
**Status:** done
**Type:** build

## Goal

Tag and rank humanoid pilot language on pipeline leads — distinct "humanoid readiness" lane.

## Acceptance criteria

- [x] `humanoid_pilot_ranking.py` — tier/score/label/action from signals
- [x] Pipeline cards expose `humanoid_pilot_*` fields; humanoid leads boost next-actions
- [x] Pipeline UI humanoid badge + next-actions chip
- [x] Tests; cache rebuild; commit, push, deploy, notify

## Context

Bet #5 in market thesis; builds on ontology `humanoid_deployment` + catalog asset.

## Out of scope

- Re-scoring global HOT/WARM tiers
- Humanoid benchmark page redesign
