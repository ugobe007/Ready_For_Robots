# VinMotion FIND report

**Date:** 2026-08-31
**Branch:** `cursor/vinmotion-oem-009b`
**Verdict:** critic corpus **20/20 PASS**, 0 breaks. Fixtures **8/8 PASS**. VinMotion n=2.

This is the report. You do not need a terminal to read it.

Operator URL: https://vinmotion.net/

Rule held: company → product → configuration → hardware → capabilities. Never company → category.

## Named products

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Motion 1 | humanoid | mobile, manipulate | https://vinmotion.net/ and https://vinmotion.net/product/motion-1. Homepage copy: "VinMotion Motion 1 humanoid robot." |
| Motion 2 | unclassified | none | https://vinmotion.net/ and https://vinmotion.net/product/motion-2. Homepage: "Motion 2 launching." Product page is a hero video only. |

Not SKUs: Product, About, Careers, News, VinMotion Humanoid.

## Critic

```
[PASS] https://vinmotion.net/
  range=['humanoid'] mixed=False Motion 1=humanoid, Motion 2=None
```

`expects_named_robots: true`. Empty would BREAK.

Fixtures 8/8 PASS. Other corpus OEMs unchanged (Tennant 5, SEER 7, Pudu mixed serving/cleaning/humanoid).

## Files

- `ontology/mixed_oem_sku_catalog.v1.json` (cache)
- `app/data/vendor_robots_oem_sku_seed.json`
- `readyforrobots-new/client/src/lib/knownOemLineups.json`
- `app/data/url_workflow_corpus.json`
- `app/services/oem_sku_discover.py` (listing hints + next_f ProductMenuItem)

## Not deployed

Fly still does not know this OEM until someone deploys. Catalog path is local. Do not merge #195.
