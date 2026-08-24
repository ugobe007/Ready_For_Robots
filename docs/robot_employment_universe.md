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
| Robot | Up to 3 names from existing catalogs | SKUs not in the catalog |
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
| [`../scripts/compile_employment_universe.py`](../scripts/compile_employment_universe.py) | Resolve websites + ≤3 catalog names, fill from named-product seed OEMs |

Rebuild:

```bash
python3 scripts/compile_employment_universe.py
```

Core companies with `robots: []` still belong in the universe. They are placeable-labor OEMs whose **product names are not in our catalog yet**. Fill those names from the OEM site (max 3, never generic “AGV/AMR”), then recompile. Do not paste the roster into ChatGPT and ask it to invent models.

## Relation to FIND

FIND still looks up a pasted OEM URL against host-normalized catalogs. This universe is the **employment overlay**: which companies are candidates, which categories they hire into, which named robots we already know. It does not replace Understanding v1 or the matcher.
