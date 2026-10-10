# URL workflow critic report

**Date:** 2026-08-31  
**Branch:** `cursor/url-workflow-critic-009b` (PR #198), VinMotion addendum on `cursor/vinmotion-oem-009b`  
**Verdict:** catalog corpus **20/20 PASS** after VinMotion. Fixtures **8/8 PASS**. Tennant 5 named robots. SEER 7. VinMotion 2.

This is the report. You do not need a terminal to read it.

VinMotion operator review lives in `missions/2026-08-31-vinmotion/REVIEW.md`.

FIND identity was driven for every OEM in the operator list: product range, named products, per-product capabilities. Catalog path (indexed listing). Live Fly still shows stale junk until this branch deploys. Empty Tennant or SEER is now a critic break.

Rule held: company → product → configuration → hardware → capabilities. Never company → category → jobs.

## What was tested

19 OEM URLs from `app/data/url_workflow_corpus.json`, plus VinMotion as #20:

| # | OEM | URL |
|---|-----|-----|
| 1 | Pringle Robotics | https://pringlerobotics.ai/ |
| 2 | Keenon | https://www.keenon.com/en |
| 3 | Pudu Robotics | https://www.pudurobotics.com/en |
| 4 | Bear Robotics | https://www.bearrobotics.ai/ |
| 5 | Aotingbots | https://www.aotingbot.com/ |
| 6 | Kärcher | https://www.kaercher.com/us/ |
| 7 | Richtech | https://richtechrobotics.com/ |
| 8 | CenoBots | https://www.cenobots.com/ |
| 9 | Lucid Bots | https://www.lucidbots.com/ |
| 10 | Tennant | https://www.tennantco.com/en_us.html |
| 11 | ECOVACS Commercial | https://www.ecovacscommercial.com/ |
| 12 | SEER Robotics | https://seer-robotics.ai/ |
| 13 | Avidbots | https://avidbots.com/ |
| 14 | Gausium | https://gausium.com/ |
| 15 | PolarX Robotics | https://www.polarxrobotics.com/ |
| 16 | UBTECH | https://www.ubtrobot.com/ |
| 17 | AgiBot | https://www.agibot.com/ |
| 18 | MagicLab | https://www.magiclab.top/ |
| 19 | Deep Robotics | https://www.deeprobotics.cn/ |
| 20 | VinMotion | https://vinmotion.net/ |

Fixtures (synthetic breaks, CI gate `url_workflow`): mixed-range flattened, chrome-as-SKU, cleaning-drone-as-scrubber, company-class-not-product-class, empty known-OEM hub, class-dump SKU, healthy mixed, healthy drone.

## Scoreboard

| OEM | Range | n | Result | Note |
|-----|-------|---|--------|------|
| Pringle Robotics | serving, cleaning | 11 | PASS | BellaBot serving vs CC1 cleaning stay distinct |
| Keenon | serving, hospitality, cleaning, humanoid | 17 | PASS | T11 serving vs C55 cleaning. Peanut, M2, S300, S100 unclassified |
| Pudu Robotics | serving, cleaning, humanoid | 12 | PASS | BellaBot / CC1 / D9 distinct. FlashBot and PUDU* thin |
| Bear Robotics | serving, amr, cleaning | 8 | PASS | Servi vs Servi Clean. Generic Carti unclassified |
| Aotingbots | cleaning | 2 | PASS | SW80 A, SW55 A |
| Kärcher | cleaning | 4 | PASS | KIRA robotic line only, not every mop |
| Richtech | serving, cleaning | 11 | PASS | ADAM and Scotty serving, DUST-E MX cleaning. 8 thin SKUs |
| CenoBots | cleaning | 5 | PASS | S5 and L-series |
| Lucid Bots | cleaning_drone | 2 | PASS | Sherpa has `drone_task`, not floor-scrub |
| Tennant | cleaning | 5 | PASS | X6 ROVR, X16 SWEEP, T7AMR, T380AMR, T16AMR. Empty would now BREAK |
| ECOVACS Commercial | cleaning | 2 | PASS | DEEBOT PRO M1 / K1 VAC |
| SEER Robotics | amr | 7 | PASS | AMB / SFL / SCB named. SRC-880 thin. No Seer Humanoid |
| Avidbots | cleaning | 3 | PASS | Neo, Neo 2W, Kas |
| Gausium | cleaning | 14 | PASS | Named Scrubber 50/75 kept. Generic `Scrubber` gone. 5 thin SKUs |
| PolarX Robotics | cleaning | 3 | PASS | Star50 / 60 / 40 |
| UBTECH | humanoid | 9 | PASS | Walker stays humanoid. Cruzr unclassified |
| AgiBot | humanoid | 6 | PASS | No serving dump |
| MagicLab | humanoid, quadruped | 3 | PASS | MagicBot vs MagicDog |
| Deep Robotics | humanoid, quadruped | 4 | PASS | DR02 humanoid vs X20/X30 quadruped |
| VinMotion | humanoid | 2 | PASS | Motion 1 humanoid. Motion 2 launching page unclassified. No invented SKU |

**20/20 PASS. 0 breaks.**

## Per URL: products and capabilities

Capabilities omit the internal `classes` flag.

### Pringle Robotics. PASS

https://pringlerobotics.ai/ · range serving, cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| BellaBot | serving | mobile, serving_task |
| BellaBot PRO | serving | mobile, serving_task |
| KettyBot | serving | mobile, serving_task |
| HolaBot | serving | mobile, serving_task |
| PuduBot 2 | serving | mobile, serving_task |
| CC1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| CC1 PRO | cleaning | hard_floor_scrub, mobile, surface_clean |
| CC3 | cleaning | hard_floor_scrub, mobile, surface_clean |
| CC5 | cleaning | hard_floor_scrub, mobile, surface_clean |
| PUDU T300 | cleaning | hard_floor_scrub, mobile, surface_clean |
| MT-1 | cleaning | hard_floor_scrub, mobile, surface_clean |

### Keenon. PASS

https://www.keenon.com/en · range serving, hospitality, cleaning, humanoid

| Product | Class | Capabilities |
|---------|-------|--------------|
| Keenon T8 | serving | mobile, serving_task |
| Peanut | unclassified | none |
| Dinerbot T10 | serving | mobile, serving_task |
| Dinerbot T5 | serving | mobile, serving_task |
| Butlerbot W3 | hospitality | hospitality_task, mobile |
| Keenon C30 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Keenon M2 | unclassified | none |
| T11 | serving | mobile, serving_task |
| C55 | cleaning | hard_floor_scrub, mobile, surface_clean |
| C40 | cleaning | hard_floor_scrub, mobile, surface_clean |
| C20 | cleaning | hard_floor_scrub, mobile, surface_clean |
| T9 | serving | mobile, serving_task |
| T3 | serving | mobile, serving_task |
| XMAN-R1 | humanoid | manipulate, mobile |
| XMAN-F1 | humanoid | manipulate, mobile |
| S300 | unclassified | none |
| S100 | unclassified | none |

### Pudu Robotics. PASS

https://www.pudurobotics.com/en · range serving, cleaning, humanoid

| Product | Class | Capabilities |
|---------|-------|--------------|
| BellaBot | serving | mobile, serving_task |
| PuduBot 2 | serving | mobile, serving_task |
| KettyBot | serving | mobile, serving_task |
| HolaBot | serving | mobile, serving_task |
| FlashBot | unclassified | none |
| CC1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| MT1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| PUDU T300 | cleaning | hard_floor_scrub, mobile, surface_clean |
| D9 | humanoid | manipulate, mobile |
| PUDUA1 | unclassified | none |
| PUDUD1 | unclassified | none |
| PUDUSH1 | unclassified | none |

### Bear Robotics. PASS

https://www.bearrobotics.ai/ · range serving, amr, cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| Servi | serving | mobile, serving_task |
| Servi Plus | serving | mobile, serving_task |
| Carti 100 | amr | mobile, transport |
| Carti High Payload | amr | mobile, transport |
| Carti | unclassified | none |
| Servi Q | serving | mobile, serving_task |
| Servi Clean | cleaning | hard_floor_scrub, mobile, surface_clean |
| Servi Clean Max | cleaning | hard_floor_scrub, mobile, surface_clean |

### Aotingbots. PASS

https://www.aotingbot.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| SW80 A | cleaning | hard_floor_scrub, mobile, surface_clean |
| SW55 A | cleaning | hard_floor_scrub, mobile, surface_clean |

### Kärcher. PASS

https://www.kaercher.com/us/ · range cleaning

KIRA robotic line only. Pressure washers and mops stay out.

| Product | Class | Capabilities |
|---------|-------|--------------|
| KIRA B 50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| KIRA B 200 | cleaning | hard_floor_scrub, mobile, surface_clean |
| KIRA CV 50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| KIRA CV 60/1 | cleaning | hard_floor_scrub, mobile, surface_clean |

### Richtech. PASS

https://richtechrobotics.com/ · range serving, cleaning

ADAM and Scotty are real. Most of the rest is a thin SKU list with no class and no capabilities. That is a gap, not a critic break.

| Product | Class | Capabilities |
|---------|-------|--------------|
| ADAM | serving | mobile, serving_task |
| MATRADEE | unclassified | none |
| MATRADEE X | unclassified | none |
| MATRADEE L | unclassified | none |
| LUCKI | unclassified | none |
| MEDBOT | unclassified | none |
| DUST-E MX | cleaning | hard_floor_scrub, mobile, surface_clean |
| AIDY | unclassified | none |
| Scorpion | unclassified | none |
| Titan | unclassified | none |
| Scotty | serving | mobile, serving_task |

### CenoBots. PASS

https://www.cenobots.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| S5 | cleaning | hard_floor_scrub, mobile, surface_clean |
| L3 | cleaning | hard_floor_scrub, mobile, surface_clean |
| L4 | cleaning | hard_floor_scrub, mobile, surface_clean |
| L50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| SP50 | cleaning | hard_floor_scrub, mobile, surface_clean |

### Lucid Bots. PASS (was BREAK)

https://www.lucidbots.com/ · range cleaning_drone

First pass failed: Sherpa inherited OEM floor-scrub defaults and missed `drone_task`. After the fix, both SKUs are cleaning drones with drone work, not scrubbers.

| Product | Class | Capabilities |
|---------|-------|--------------|
| Sherpa Drone | cleaning_drone | avionics_task, drone_task, mobile |
| Sherpa Drone NDAA | cleaning_drone | avionics_task, drone_task, mobile |

### Tennant. PASS (was empty, now named robots)

https://www.tennantco.com/en_us.html · range cleaning · 5 products

The hub used to pass with 0 products. That was the bug. Live robotics pages name these SKUs. We did not put back `AMR scrubbers` or a generic `Scrubber`. Ride-on T7 without AMR stays out.

Evidence:
- https://www.tennantco.com/en_us/robotics.html (X6 ROVR, X16 SWEEP)
- https://www.tennantco.com/en_us/1/machines/scrubbers/product.x6-rovr.autonomous-floor-scrubber.m-x6rovr.html
- https://www.tennantco.com/en_us/1/machines/sweepers/product.X16-sweep.autonomous-floor-sweeper.2000309.html
- https://www.tennantco.com/en_us/1/machines/scrubbers/product.t7amr.robotic-floor-scrubber.2000056.html
- https://www.tennantco.com/en_us/1/machines/scrubbers/product.t380amr.robotic-floor-scrubber.2000055.html
- https://www.tennantco.com/en_us/1/machines/scrubbers/product.t16amr.industrial-robotic-floor-scrubber.2000054.html

| Product | Class | Capabilities |
|---------|-------|--------------|
| X6 ROVR | cleaning | hard_floor_scrub, mobile, surface_clean |
| X16 SWEEP | cleaning | hard_floor_scrub, mobile, surface_clean |
| T7AMR | cleaning | hard_floor_scrub, mobile, surface_clean |
| T380AMR | cleaning | hard_floor_scrub, mobile, surface_clean |
| T16AMR | cleaning | hard_floor_scrub, mobile, surface_clean |

### ECOVACS Commercial. PASS

https://www.ecovacscommercial.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| DEEBOT PRO M1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| DEEBOT PRO K1 VAC | cleaning | hard_floor_scrub, mobile, surface_clean |

### SEER Robotics. PASS (was empty, now named robots)

https://seer-robotics.ai/ · range amr · 7 products

`Seer Humanoid` stays out. It was a company+morphology dump. Live category pages name AMB lifting AMRs, SFL/SCB vehicles, and SRC-880 (controller, unclassified).

Evidence:
- https://seer-robotics.ai/amr/liftingrobot (AMB-300JZ, AMB-300XS, SJV-SW600)
- https://seer-robotics.ai/amr/liftingrobot/AMB-300JZ
- https://seer-robotics.ai/amr/autonomousforklifts (SFL-CBD15, SFL-300L, SCB-1400)
- https://seer-robotics.ai/amr/autonomousforklifts/SFL-CBD15
- https://seer-robotics.ai/amr-controllers/SRC-880

| Product | Class | Capabilities |
|---------|-------|--------------|
| AMB-300JZ | amr | mobile, transport |
| AMB-300XS | amr | mobile, transport |
| SJV-SW600 | amr | mobile, transport |
| SFL-CBD15 | amr | mobile, transport |
| SFL-300L | amr | mobile, transport |
| SCB-1400 | amr | mobile, transport |
| SRC-880 | unclassified | none |

### Avidbots. PASS

https://avidbots.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| Neo | cleaning | hard_floor_scrub, mobile, surface_clean |
| Neo 2W | cleaning | hard_floor_scrub, mobile, surface_clean |
| Kas | cleaning | hard_floor_scrub, mobile, surface_clean |

### Gausium. PASS (was BREAK)

https://gausium.com/ · range cleaning

First pass listed generic `Scrubber` as a SKU. Named Scrubber 50 and Scrubber 75 stay. Generic dump is gone. CD/WS rows are still thin.

| Product | Class | Capabilities |
|---------|-------|--------------|
| Phantas | cleaning | hard_floor_scrub, mobile, surface_clean |
| Vacuum 40 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Scrubber 50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Scrubber 75 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Beetle | cleaning | hard_floor_scrub, mobile, surface_clean |
| Mira | cleaning | hard_floor_scrub, mobile, surface_clean |
| Marvel | cleaning | hard_floor_scrub, mobile, surface_clean |
| Omnie | cleaning | hard_floor_scrub, mobile, surface_clean |
| PhanShop | cleaning | hard_floor_scrub, mobile, surface_clean |
| CD-01 | unclassified | none |
| CD-04 | unclassified | none |
| WS-01 | unclassified | none |
| WS-02 | unclassified | none |
| WS-03 | unclassified | none |

### PolarX Robotics. PASS

https://www.polarxrobotics.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| Star50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Star60 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Star40 | cleaning | hard_floor_scrub, mobile, surface_clean |

### UBTECH. PASS

https://www.ubtrobot.com/ · range humanoid

Walker is humanoid, not a serving robot. Cruzr has no class yet.

| Product | Class | Capabilities |
|---------|-------|--------------|
| UBTECH Walker X | humanoid | manipulate, mobile |
| U1 Pro | humanoid | manipulate, mobile |
| UBTECH Walker S2 | humanoid | manipulate, mobile |
| U1 Lite | humanoid | manipulate, mobile |
| U1 Ultra | humanoid | manipulate, mobile |
| UBTECH Walker S | humanoid | manipulate, mobile |
| Cruzr | unclassified | none |
| Walker | humanoid | manipulate, mobile |
| Alpha 1E | humanoid | manipulate, mobile |

### AgiBot. PASS

https://www.agibot.com/ · range humanoid

| Product | Class | Capabilities |
|---------|-------|--------------|
| A3 Ultra | humanoid | manipulate, mobile |
| Agibot A2 | humanoid | manipulate, mobile |
| Agibot G5 | humanoid | manipulate, mobile |
| G2 humanoid robot | humanoid | manipulate, mobile |
| X2 | humanoid | manipulate, mobile |
| AGIBOT G1 | humanoid | manipulate, mobile |

### MagicLab. PASS

https://www.magiclab.top/ · range humanoid, quadruped

| Product | Class | Capabilities |
|---------|-------|--------------|
| MagicLab MagicBot Gen1 | humanoid | manipulate, mobile |
| MagicBot X1 | humanoid | manipulate, mobile |
| MagicDog | quadruped | inspect_route, mobile |

### Deep Robotics. PASS

https://www.deeprobotics.cn/ · range humanoid, quadruped

| Product | Class | Capabilities |
|---------|-------|--------------|
| Deep Robotics DR02 | humanoid | manipulate, mobile |
| Deep Robotics DR01 | humanoid | manipulate, mobile |
| X20 | quadruped | inspect_route, mobile |
| X30 | quadruped | inspect_route, mobile |

### VinMotion. PASS

https://vinmotion.net/ · range humanoid · 2 products

| Product | Class | Capabilities |
|---------|-------|--------------|
| Motion 1 | humanoid | manipulate, mobile |
| Motion 2 | unclassified | none |

Evidence: homepage Product menu and https://vinmotion.net/product/motion-1 / https://vinmotion.net/product/motion-2. Motion 1 is named a humanoid robot on the homepage. Motion 2 launching page has no hardware copy. Full write-up: `missions/2026-08-31-vinmotion/REVIEW.md`.

## What broke (first catalog pass)

| URL | Break | Detail |
|-----|-------|--------|
| https://www.lucidbots.com/ | capability_oem_default | Sherpa Drone missing `drone_task`. Inherited scrub-class defaults. |
| https://seer-robotics.ai/ | invented_sku | `Seer Humanoid` is a category dump, not a SKU |
| https://seer-robotics.ai/ | invented_sku | forbidden SKU `Seer Humanoid` present |
| https://seer-robotics.ai/ | company_class_not_product_class | Seer Humanoid class `humanoid` forbidden on this hub |
| https://gausium.com/ | invented_sku | generic `Scrubber` is a category dump, not a SKU |
| https://gausium.com/ | invented_sku | forbidden SKU `Scrubber` present |

6 breaks. Mixed F&B (Pringle, Keenon, Pudu, Bear) and UBTECH / AgiBot / MagicLab / Deep Robotics were already PASS on range and named evidence SKUs.

Fixtures already catch the same classes of lie: flattening mixed lines to `service_robot`, treating About/Products/News as SKUs, calling a facade drone a floor scrubber, putting BellaBot and CC1 in one company class.

## What was fixed

- `cleaning_drone` counts as a drone class, so Sherpa grounds `drone_task` instead of `hard_floor_scrub`.
- Junk SKU names: company+morphology dumps (`Seer Humanoid`), generic `Scrubber`, `AMR scrubbers`.
- Catalog cache: PuduBot 2 serving; Diligent Moxi healthcare; drop class-dump lineups; Gausium keeps named models only.
- Prefer overlay-specific class over generic `service_robot`.
- Discovered SKUs no longer inherit a sibling's `primary_class`.
- Live overlay ignores stale Fly junk until this branch deploys.

## Reconfirm

| Gate | Result |
|------|--------|
| Fixtures | 8/8 PASS, exit 0 (empty OEM hub and class-dump SKU now fail on purpose) |
| Catalog corpus | **20/20 PASS**, 0 breaks. VinMotion n=2. Tennant n=5, SEER n=7. Other 19 unchanged |
| pstack `url_workflow` | fixture suite green locally |
| Live Fly | still stale until this branch deploys. Critic notes junk SKUs and does not fail on them |

## Remaining gaps

1. **Fly production listing is stale.** Production still serves `AMR scrubbers` / `Seer Humanoid` / generic `Scrubber`. Catalog on this branch is the source of truth until deploy.
2. **Thin SKUs.** Named but unclassified, no capabilities: Keenon Peanut / M2 / S300 / S100; Pudu FlashBot / PUDUA1 / PUDUD1 / PUDUSH1; Bear Carti; Richtech MATRADEE family, LUCKI, MEDBOT, AIDY, Scorpion, Titan; Gausium CD/WS series; UBTECH Cruzr; SEER SRC-880; VinMotion Motion 2. They do not fail the critic. They also do not help matching. They do not inherit a sibling class.
3. **Kärcher hub is KIRA only.** Correct for robotic cleaning. The rest of the Kärcher catalog is not robots.
4. **Tennant X16 SWEEP** is a sweeper. It still grounds `hard_floor_scrub` because the FIND class is cleaning. Fine for this critic. Not a second matcher.
5. Do not merge #195.

The human review docs are `missions/2026-08-31-url-workflow-critic/REVIEW.md` and `missions/2026-08-31-vinmotion/REVIEW.md`.
