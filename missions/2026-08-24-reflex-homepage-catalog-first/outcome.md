# Outcome — Indexed OEM homepages skip live fetch (systemic)

**Date:** 2026-08-24
**Status:** code complete; production Fly still on previous revision until merge/deploy

## Is this Reflex-only?

No. The vendor index has **21 multi-SKU OEMs** whose every `product_url` is the homepage (Figure, UBTECH, EngineAI, Sanctuary, Reflex, …) and **45 homepage-only vendors**. Cloudflare/WAF delays are normal on robot OEM sites. FIND must not wait on those hosts when the catalog already has SKUs.

## Fix

- Indexed vendor URLs (homepage or SKU) skip `fetch_page` for **every** catalog OEM, not only Reflex.
- Unknown OEMs may still crawl, but homepage fetch and source pack share one wall-clock budget (default 12s) so FIND's 22s client abort cannot fire from additive timeouts.
- Timeout copy no longer tells the user they pasted the wrong kind of URL.

## Metrics

- `build_robot_profile` on indexed homepages: `home_fetch=skipped` (50+ vendors in test).
- Reflex: picker in ~5ms (Gen2 + Humanoid).
- pytest: catalog-first + vendor lookup suite green.

## Follow-ups

Deploy `ready-2-robot` after merge. Index misses (OEM not in the catalog) still crawl live under the 12s budget.
