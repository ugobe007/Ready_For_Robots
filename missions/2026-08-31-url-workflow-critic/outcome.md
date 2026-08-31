# Outcome — URL workflow critic

**Date:** 2026-08-31
**Branch:** `cursor/url-workflow-critic-009b`
**Status:** complete (catalog critic green; Fly production still pre-deploy)

## How to run

```bash
python3 scripts/url_workflow_critic.py --fixtures
python3 scripts/url_workflow_critic.py
python3 scripts/url_workflow_critic.py --out reports/url_workflow_critic.json   # do not commit
python3 scripts/url_workflow_critic.py --live   # optional Fly POST /api/robot-job-search
python3 scripts/pstack_release.py --local
```

Exit non-zero on breaks. CI uses fixtures (`pstack` gate `url_workflow`). Pytest does not import fetch/facts.

## Breaks found (catalog, first pass)

| URL | Range | Products | Capabilities |
|-----|-------|----------|--------------|
| Lucidbots | PASS `cleaning_drone` | Sherpa Drone named | **BREAK** `capability_oem_default` — missing `drone_task` (scrub-class default) |
| SEER | — | **BREAK** invented `Seer Humanoid` | company-class dump |
| Gausium | PASS cleaning | **BREAK** generic `Scrubber` as SKU (named `Scrubber 50/75` kept) | — |
| Tennant | empty (honest picker) | PASS — no T7AMR / AMR scrubbers | — |
| Operator mixed F&B + UBTech / AgiBot / MagicLab / Deep Robotics | PASS distinct classes | named evidence SKUs | per-product |

Fixtures already covered mixed-range-flattened, chrome-as-SKU, cleaning-drone-as-scrubber, company-class-not-product-class.

## Fixes shipped

- `cleaning_drone` in `DRONE_CLASSES` / `AVIONICS_CLASSES` so Sherpa grounds `drone_task`, not `hard_floor_scrub`.
- Junk SKU names: company+morphology dumps (`Seer Humanoid`), generic `Scrubber`, `AMR scrubbers`.
- Catalog cache: PuduBot 2 serving; Diligent Moxi healthcare; drop class-dump lineups; Gausium keeps named models only.
- Prefer overlay-specific class over generic `service_robot`.
- Live overlay ignores stale Fly junk SKUs until this branch deploys.

## Reconfirm

- Fixtures: exit 0, six cases PASS.
- Corpus: **19/19 PASS**, 0 breaks.
- Live sample (Lucidbots, Pudu, Tennant, SEER, Gausium): **ok=True** after junk overlay. Fly still *returns* `AMR scrubbers` / `Seer Humanoid` / generic `Scrubber` until deploy — critic notes them as junk, does not fail.
- pytest critic + mixed-OEM + pstack: green. vitest knownOemLineups / jobsWorkflow / pstack: 54 passed.
- `pstack_release.py --local` `url_workflow` green.

## Gaps

- Fly production listing is pre-this-branch. Tennant/SEER stay empty locally (class picker), which is honest — do not invent T7AMR.
- Richtech/Keenon thin SKUs may be unclassified (`None`) rather than OEM-default serving.
- Kaercher hub is KIRA robotic line only.
- Do not merge #195.
- `ManagePullRequest` is not in this agent catalog; draft PR via `gh` if permitted.

## Product rules held

`/` = Jobs FIND. Identity keyed to submitted URL. Evidence SKUs only. Catalog is cache; page extract wins. No invented economics. No Apollo/SIGNAL hop.
