# Outcome. URL workflow critic

**Date:** 2026-08-31
**Branch:** `cursor/url-workflow-critic-009b`
**Status:** complete (catalog critic green with named Tennant/SEER robots; Fly production still pre-deploy)

**Read this:** [`REVIEW.md`](REVIEW.md) (short) and [`report.md`](report.md) (scoreboard). Do not use the PR body as the report.

## Breaks found (catalog, first pass)

| URL | Range | Products | Capabilities |
|-----|-------|----------|--------------|
| Lucidbots | PASS `cleaning_drone` | Sherpa Drone named | **BREAK** `capability_oem_default`, missing `drone_task` (scrub-class default) |
| SEER | empty then invented `Seer Humanoid` | **BREAK** company-class dump |  |
| Gausium | PASS cleaning | **BREAK** generic `Scrubber` as SKU (named `Scrubber 50/75` kept) |  |
| Tennant | empty treated as PASS | **BREAK** once empty OEM hubs fail |  |

Operator mixed F&B + UBTech / AgiBot / MagicLab / Deep Robotics were already PASS.

## This pass

Tennant: X6 ROVR, X16 SWEEP, T7AMR, T380AMR, T16AMR. SEER: AMB-300JZ, AMB-300XS, SJV-SW600, SFL-CBD15, SFL-300L, SCB-1400, SRC-880. Empty known OEM is `empty_range_on_robot_oem`.

## Fixes shipped

- `cleaning_drone` in `DRONE_CLASSES` / `AVIONICS_CLASSES` so Sherpa grounds `drone_task`, not `hard_floor_scrub`.
- Junk SKU names: company+morphology dumps (`Seer Humanoid`), generic `Scrubber`, `AMR scrubbers`.
- Catalog cache: PuduBot 2 serving; Diligent Moxi healthcare; drop class-dump lineups; Gausium keeps named models only; Tennant/SEER named robots from live pages.
- Empty robot-OEM hub is a critic break. Class-dump names still break.
- Prefer overlay-specific class over generic `service_robot`.
- Live overlay ignores stale Fly junk SKUs until this branch deploys.

## Reconfirm

- Fixtures: 8/8 PASS (empty OEM + class dump added).
- Corpus: **19/19 PASS**, 0 breaks. Tennant n=5, SEER n=7.
- Fly still returns `AMR scrubbers` / `Seer Humanoid` / generic `Scrubber` until deploy.
- pytest critic + mixed-OEM: 32 passed.

## Gaps

- Fly production listing is pre-this-branch. Deploy before treating production FIND as truth.
- Richtech/Keenon thin SKUs may be unclassified (`None`) rather than OEM-default serving.
- Kaercher hub is KIRA robotic line only.
- Do not merge #195.

## Product rules held

`/` = Jobs FIND. Identity keyed to submitted URL. Evidence SKUs only. Catalog is cache; page extract wins. No invented economics. No Apollo/SIGNAL hop.
