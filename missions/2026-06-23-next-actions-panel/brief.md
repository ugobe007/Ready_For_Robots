# Mission: Next actions panel

**Date:** 2026-06-23
**Agent:** ProductSurface
**Status:** done
**Type:** build

## Goal

Home right rail: top 3 autonomous pipeline actions from live SIGNAL feed (UX doc §4).

## Acceptance criteria

- [x] `GET /api/leads/pipeline-next-actions` — top 3 ranked actions from pipeline cache
- [x] `NextActionsPanel` on home hero right column + pipeline surface
- [x] Tests; deploy; commit, push, notify

## Context

- Builds on `pipeline-action-copy` (`pipeline_action` on cards)
- UX north star: Advance, not browse (`docs/readyforrobots-ux.md`)

## Out of scope

- CRM/sales-workflow merge (authenticated `/api/sales/next-actions` stays separate)
- Activity feed redesign
