# Vendor robots URL lookup backfill

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface + LeadQuality (identity) — no SIGNAL/CRM expansion  
**ICP:** Robot OEM submits homepage on Jobs FIND → stored SKUs, not guessed crawl  

## Goal

Scrape every robot on https://readyforrobots.com/robots (`GET /api/humanoid/robots`), build a lightweight profile per SKU, and persist a vendor-domain lookup so Jobs URL submit returns that vendor's robots when the host matches.

Until URL lookup is rock-solid, the JSON index is the source of truth. `--apply` upserts existing `manufacturers` / `robot_models` when `DATABASE_URL` is set. Industrial and commercial lists later reuse the same `list_category` shape.

## Acceptance

1. Script `scripts/backfill_vendor_robots_from_index.py` writes `app/data/vendor_robots_index.json` from the live `/robots` API.
2. Press hosts (Morningstar, TMCnet, Yahoo, Reuters, MSN, …) are never lookup keys.
3. `unitree.com` / `engineai.com` + `engineai.com.cn` / `ubtrobot.com` return stored SKUs without homepage guessing.
4. `resolve_identity` merges index names first; homepage crawl may add extras.
5. Vendor homepage and locale root (`/en`) do not auto-select a SKU.
6. Targeted pytest green. No Fly deploy required in this environment.

## Out of scope

- Live crawl of 129 OEM sites
- Qualify / Place / SIGNAL as core expansion
- New Alembic revision (multiple heads)
- Industrial / commercial ontology lists (same JSON shape later)
