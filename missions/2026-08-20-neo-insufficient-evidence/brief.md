# Mission: 1X NEO — insufficient robot evidence

**Date:** 2026-08-20
**Type:** build (Understanding integrity)
**Agent:** Understanding + Jobs

## Goal

A Jobs search for 1X NEO (`https://www.1x.tech/neo`) returned the honest
zero-state **Insufficient robot evidence**. The UI is correct not to invent
jobs. The failure is Understanding: manufacturer evidence exists and was not
grounded.

## Observed production profile

- Identity: company 1X, product Neo — correct
- Grounded facts: payload 18 lb, IP68/IP44 only
- `product_class` / mobility / autonomy: UNKNOWN
- `research_morphology`: quadruped (wrong — IP + payload heuristic)
- `inference`: null (`ROBOT_INFERENCE_ENGINE` off in Fly)
- Cache: 6h reuse of this C/low profile (`cached: true`)

Root cause: 1X is a Next.js page. “NEO is a fully electronic humanoid robot”
lives in `application/json`, which `_html_to_text` stripped with every
`<script>`. v1 extractors never saw `humanoid`. The authorized 2026-08-18
inference engine never ran.

## In scope (Phases 1–3 integrity)

- Collect Next.js / JSON-LD string evidence into page text (source collection)
- Enable `ROBOT_INFERENCE_ENGINE=1` in Fly
- Do not cache / reuse low-coverage profiles
- Stop treating IP + payload as quadruped
- Ground “works autonomously” as navigation evidence

## Out of scope

- Matcher reopen / corpus expansion
- LLM profile generation
- Per-vendor 1X branches
- Blind 20 extractor retune

## Acceptance

- Embedded JSON containing “humanoid robot” becomes page text
- Engine on 1X-like copy grounds `product_class=humanoid` → manipulate
- Low-coverage profiles are not cached
- IP + payload ≠ quadruped
- Targeted pytest passes
