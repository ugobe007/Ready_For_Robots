# Mixed OEM product range (humanoid + serving + cleaning + quadruped)

**Date:** 2026-08-31
**Type:** build
**Agents:** ProductSurface + ontology
**Status:** complete on branch (Fly production not yet deployed)
**Branch:** `cursor/mixed-oem-product-range-009b`

## Goal

PUDU, Keenon, UBTech, AgiBot, MagicLab, DeepRobotics (and catalog peers) ship **humanoids, service/serving robots, AND cleaning robots** (Deep Robotics also ships quadrupeds). FIND must recognize the **company product range** and **each named product** from page/catalog evidence — never collapse the OEM to one class (`service_robot`) or fall through to the type picker when the page names SKUs.

Tiny loop: robot URL → credible jobs.

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → JOB REQUIREMENTS → MATCH
```

Never `company → category → jobs`.

## Operator ask

"PUDU, Keenon, UBTech, AgiBot, MagicLab, DeepRobotics and others make humanoids, service robots and cleaning robots so we need to recognize their product range and their products"

Cleaning + mixed F&B operator list (live page evidence; mixed OEMs classified per product, not company): Pringle, Keenon, Pudu, Bear, Aoting, Kaercher (robotic KIRA only), Richtech, CenoBots, Lucidbots (**cleaning drones**, not floor scrubbers), Tennant, Ecovacs Commercial, SEER, Avidbots, Gausium, PolarX.

## Acceptance

1. Company hub (pudurobotics.com/en, keenon.com, ubtrobot.com, agibot.com, magiclab.top, deeprobotics.cn) lists **named products** with **distinct classes**.
2. BellaBot serving, CC1 cleaning, D9 humanoid (official D9 page is a full-sized bipedal humanoid).
3. Keenon Dinerbot/T11 serving vs C30/C55 cleaning.
4. UBTech Walker humanoid, not a waiter.
5. AgiBot / MagicLab humanoid SKUs are not waiters. MagicLab MagicDog is quadruped (official /en/dog).
6. Deep Robotics: X20/X30 quadruped (official product pages) AND DR02 humanoid (official dr02.html). Do not invent Lite3 without a product URL in this pass.
7. Catalog overlay is cache; live extract still wins. No invented SKUs, pay, employers, or emails.
8. Tests do not import fetch/facts (pytest-only venv has no `requests`).
9. pstack release gate for this FIND/class change. `cleaning_drone` is a configuration class, not a 21st FIND tile.
10. Lucidbots Sherpa = `cleaning_drone`. Pudu BellaBot serving vs CC1 cleaning. Keenon waiter vs cleaner. Bear Servi serving vs Servi Clean cleaning. Gausium / Avidbots / Ecovacs commercial = floor `cleaning`.

## Out of scope

#195 merge. Fly deploy. Invented PuduBot 3 / MagicBot Z1 without a verified product URL. SIGNAL hop.
