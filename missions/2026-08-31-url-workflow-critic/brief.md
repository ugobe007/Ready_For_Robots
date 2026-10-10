# URL workflow critic — FIND identity breaks (range / products / capabilities)

**Date:** 2026-08-31
**Type:** build
**Agents:** ProductSurface + ontology + Deploy
**Status:** complete
**Branch:** `cursor/url-workflow-critic-009b`

## Goal

A durable agent that drives OEM URLs through the FIND / robot-understanding path, reports logic breaks (product range, named products, per-product capabilities), fails CI when they exist, then we fix extract/classify/catalog and reconfirm.

Tiny loop: robot URL → credible jobs.

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → JOB REQUIREMENTS → MATCH
```

Never `company → category → jobs`.

## Operator ask

"ok. let's build an agent that runs URLs through the workflow to find breaks in logic. then fix the breaks and reconfirm they work. agent runs URLs--> looks for product range, products, capabilities."

## Acceptance

1. `python3 scripts/url_workflow_critic.py --fixtures` exits 0 and covers mixed-range-flattened, chrome-as-SKU, cleaning-drone-as-scrubber, company-class-not-product-class.
2. `python3 scripts/url_workflow_critic.py` runs the checked-in corpus (cleaning / mixed F&B + UBTech / AgiBot / MagicLab / Deep Robotics).
3. Per URL: product range (mixed lines keep distinct classes), products (evidence SKUs only), capabilities (this product, not OEM default).
4. Exit non-zero on breaks. Optional `--out` under `reports/` (not committed).
5. Tests do not import fetch/facts.
6. pstack release gate includes `url_workflow`.
7. After catalog/classify/capability fixes, re-run fixtures + corpus until green or document remaining live-network failures.

## Out of scope

#195 merge. Invented T7AMR / PuduBot 3. SIGNAL hop. Fly deploy required for this PR (catalog path is local).
