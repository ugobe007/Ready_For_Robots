# Robot employment universe (supply side)

**Status:** Canonical supply-side dataset (2026-08-24)  
**Product meaning:** [robot_employment_model.md](./robot_employment_model.md)  
**Ontology:** never `company → category → jobs`. Match is **robot capabilities ↔ job requirements**.

ReadyForRobots is not a robotics-technology directory. The 500-vendor seed remains a scrape/input list. The **employment universe** is the labor-market supply side we recruit against:

> ~200 robot employers/candidates and the named robots we can actually place — not 500 company pages.

The valuable query is not “show me agriculture robot companies.” It is “which robots can harvest strawberries outdoors for 10 hours in California?” That query runs at FIND time. This dataset is the **candidate roster**.

## Spine

```
Company → Robot → Robot class → Work families
        → Capabilities → Availability → Geography
        → Deployment evidence → Jobs performed → Jobs R4R can find
```

| Layer | What we store now | What we do not invent |
|-------|-------------------|------------------------|
| Company | Taxonomy name + website | — |
| Robot | All named products we already have in catalog | SKUs not in the catalog |
| Robot class | Descriptor from the catalog | Job selector |
| Work families | Only for known products (Stretch → trailer unload, FieldPrinter → construction, …) | Category-wide capability claims |
| Capabilities / specs | Copied if the catalog already has numbers | Payload, runtime, “can harvest” |
| Availability / geography | Seed `commercial_maturity` / country when present | Deployment counts |
| Jobs R4R can find | Matcher output at query time | A stored job list per OEM |

Humanoids are not equal. Figure / Agility / Apptronik / 1X sit in the same employment category as research humanoids, but **class is not a match key**. A Figure humanoid and a Dusty FieldPrinter compete for different jobs.

## Files

| Path | Role |
|------|------|
| [`calibration/robot_employment_taxonomy_v1.json`](./calibration/robot_employment_taxonomy_v1.json) | 19 employment categories + core company names (hand-authored) |
| [`calibration/robot_employment_universe_v1.json`](./calibration/robot_employment_universe_v1.json) | Compiled roster (~200 companies) |
| [`../scripts/compile_employment_universe.py`](../scripts/compile_employment_universe.py) | Resolve websites + catalog names (full lineup), fill from named-product seed OEMs |
| [`calibration/readyforrobots_robot_workforce_registry_v1.xlsx`](./calibration/readyforrobots_robot_workforce_registry_v1.xlsx) | Researcher workbook (ChatGPT). One row per company. **Not catalog.** |
| [`calibration/robot_workforce_registry_overlay_v1.json`](./calibration/robot_workforce_registry_overlay_v1.json) | Same workbook as JSON. Every product name is `researcher_claim`. |
| [`calibration/robot_workforce_registry_v1_audit.md`](./calibration/robot_workforce_registry_v1_audit.md) | Why 172 “available now” is not placement-ready |

Rebuild:

```bash
python3 scripts/compile_employment_universe.py
python3 scripts/compile_known_oem_lineups.py
```

Core companies with `robots: []` still belong in the universe. They are placeable-labor OEMs whose **product names are not in our catalog yet**. Fill those names from the OEM site (never generic “AGV/AMR”), then recompile. FIND still **surfaces three robots at a time**; do not truncate the company roster to 3. Do not paste the roster into ChatGPT and ask it to invent models.

The workforce-registry workbook is useful as a **candidate list** (new OEMs, likely SKUs, work-family language). It is one product cell per company, rubber-stamps every row as an official source, and marks 172 of 200 “available for work now.” Do not replace the compiled universe with it. Verify names on the OEM page before they enter `robots[]` or FIND.

## Relation to FIND

FIND still looks up a pasted OEM URL against host-normalized catalogs. This compiled universe is the **canonical supply roster**: which companies are candidates, which categories they hire into, which named robots we already know. It does not replace Understanding v1 or the matcher.
