# Outcome — Catalog-first Sunday Memo + named Job Cards

**Date:** 2026-08-25
**Status:** done
**Type:** build

## What shipped

FIND robot / FIND jobs now treat `https://www.sunday.ai/` as an indexed OEM: Memo is in the commercial vendor index and the local `knownOemLineups` map. Catalog vendors skip live fetch. Memo is a `service_robot` (home kitchen helper), not a bipedal office humanoid.

Job Cards require a named employer and workplace. Hospitality templates and tape duplicates now carry those fields. Incomplete rows are dropped by the matcher. The Job Card UI no longer prints `Unknown` for employer/workplace. Task-model presence stays unknown (QUALIFY honesty); kitchen jobs use a kitchen/hospitality policy slot instead of opaque "Site-specific task policy."

ADAM catalog claims now include beverage prep. Delivery SKUs (MATRADEE, Servi) include item-delivery claims so hospitality work is grounded from the index.

## Tests

- `pytest` Sunday catalog + OEM listing + task models + job search + Richtech + ontology + M2 (except pre-existing Origin/clinical test on main): 64 passed
- `vitest` Job Card + known OEM lineups + jobs workflow: 37 passed

## Follow-ups

- Production Fly needs this merge before `sunday.ai` is fast on readyforrobots.com
- `test_healthcare_eldercare_delivery_matches_transport_robots` already fails on `main` (AMR class infers `transport`) — matcher freeze, not this cycle
- New OEM URLs still scrape; keep adding them to the index after a first successful parse
