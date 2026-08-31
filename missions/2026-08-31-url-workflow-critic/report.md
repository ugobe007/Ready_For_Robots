# URL workflow critic report

**Date:** 2026-08-31  
**Branch:** `cursor/url-workflow-critic-009b` (PR #198)  
**Verdict:** catalog corpus **19/19 PASS**, 0 breaks. Fixtures **6/6 PASS**.

This is the report. You do not need a terminal to read it.

FIND identity was driven for every OEM in the operator list: product range, named products, per-product capabilities. Catalog path (indexed listing). Not a live scrape. Live Fly overlay was sampled earlier and still shows stale junk until this branch deploys.

Rule held: company → product → configuration → hardware → capabilities. Never company → category → jobs.

## What was tested

19 OEM URLs from `app/data/url_workflow_corpus.json`:

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

Fixtures (synthetic breaks, CI gate `url_workflow`): mixed-range flattened, chrome-as-SKU, cleaning-drone-as-scrubber, company-class-not-product-class, healthy mixed, healthy drone.

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
| Tennant | empty | 0 | PASS | Honest empty. No invented T7AMR / AMR scrubbers |
| ECOVACS Commercial | cleaning | 2 | PASS | DEEBOT PRO M1 / K1 VAC |
| SEER Robotics | empty | 0 | PASS | Honest empty. No invented Seer Humanoid |
| Avidbots | cleaning | 3 | PASS | Neo, Neo 2W, Kas |
| Gausium | cleaning | 14 | PASS | Named Scrubber 50/75 kept. Generic `Scrubber` gone. 5 thin SKUs |
| PolarX Robotics | cleaning | 3 | PASS | Star50 / 60 / 40 |
| UBTECH | humanoid | 9 | PASS | Walker stays humanoid. Cruzr unclassified |
| AgiBot | humanoid | 6 | PASS | No serving dump |
| MagicLab | humanoid, quadruped | 3 | PASS | MagicBot vs MagicDog |
| Deep Robotics | humanoid, quadruped | 4 | PASS | DR02 humanoid vs X20/X30 quadruped |

**19/19 PASS. 0 breaks.**

## Per URL: products and capabilities

Capabilities omit the internal `classes` flag.

### Pringle Robotics — PASS

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

### Keenon — PASS

https://www.keenon.com/en · range serving, hospitality, cleaning, humanoid

| Product | Class | Capabilities |
|---------|-------|--------------|
| Keenon T8 | serving | mobile, serving_task |
| Peanut | unclassified | — |
| Dinerbot T10 | serving | mobile, serving_task |
| Dinerbot T5 | serving | mobile, serving_task |
| Butlerbot W3 | hospitality | hospitality_task, mobile |
| Keenon C30 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Keenon M2 | unclassified | — |
| T11 | serving | mobile, serving_task |
| C55 | cleaning | hard_floor_scrub, mobile, surface_clean |
| C40 | cleaning | hard_floor_scrub, mobile, surface_clean |
| C20 | cleaning | hard_floor_scrub, mobile, surface_clean |
| T9 | serving | mobile, serving_task |
| T3 | serving | mobile, serving_task |
| XMAN-R1 | humanoid | manipulate, mobile |
| XMAN-F1 | humanoid | manipulate, mobile |
| S300 | unclassified | — |
| S100 | unclassified | — |

### Pudu Robotics — PASS

https://www.pudurobotics.com/en · range serving, cleaning, humanoid

| Product | Class | Capabilities |
|---------|-------|--------------|
| BellaBot | serving | mobile, serving_task |
| PuduBot 2 | serving | mobile, serving_task |
| KettyBot | serving | mobile, serving_task |
| HolaBot | serving | mobile, serving_task |
| FlashBot | unclassified | — |
| CC1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| MT1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| PUDU T300 | cleaning | hard_floor_scrub, mobile, surface_clean |
| D9 | humanoid | manipulate, mobile |
| PUDUA1 | unclassified | — |
| PUDUD1 | unclassified | — |
| PUDUSH1 | unclassified | — |

### Bear Robotics — PASS

https://www.bearrobotics.ai/ · range serving, amr, cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| Servi | serving | mobile, serving_task |
| Servi Plus | serving | mobile, serving_task |
| Carti 100 | amr | mobile, transport |
| Carti High Payload | amr | mobile, transport |
| Carti | unclassified | — |
| Servi Q | serving | mobile, serving_task |
| Servi Clean | cleaning | hard_floor_scrub, mobile, surface_clean |
| Servi Clean Max | cleaning | hard_floor_scrub, mobile, surface_clean |

### Aotingbots — PASS

https://www.aotingbot.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| SW80 A | cleaning | hard_floor_scrub, mobile, surface_clean |
| SW55 A | cleaning | hard_floor_scrub, mobile, surface_clean |

### Kärcher — PASS

https://www.kaercher.com/us/ · range cleaning

KIRA robotic line only. Pressure washers and mops stay out.

| Product | Class | Capabilities |
|---------|-------|--------------|
| KIRA B 50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| KIRA B 200 | cleaning | hard_floor_scrub, mobile, surface_clean |
| KIRA CV 50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| KIRA CV 60/1 | cleaning | hard_floor_scrub, mobile, surface_clean |

### Richtech — PASS

https://richtechrobotics.com/ · range serving, cleaning

ADAM and Scotty are real. Most of the rest is a thin SKU list with no class and no capabilities. That is a gap, not a critic break.

| Product | Class | Capabilities |
|---------|-------|--------------|
| ADAM | serving | mobile, serving_task |
| MATRADEE | unclassified | — |
| MATRADEE X | unclassified | — |
| MATRADEE L | unclassified | — |
| LUCKI | unclassified | — |
| MEDBOT | unclassified | — |
| DUST-E MX | cleaning | hard_floor_scrub, mobile, surface_clean |
| AIDY | unclassified | — |
| Scorpion | unclassified | — |
| Titan | unclassified | — |
| Scotty | serving | mobile, serving_task |

### CenoBots — PASS

https://www.cenobots.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| S5 | cleaning | hard_floor_scrub, mobile, surface_clean |
| L3 | cleaning | hard_floor_scrub, mobile, surface_clean |
| L4 | cleaning | hard_floor_scrub, mobile, surface_clean |
| L50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| SP50 | cleaning | hard_floor_scrub, mobile, surface_clean |

### Lucid Bots — PASS (was BREAK)

https://www.lucidbots.com/ · range cleaning_drone

First pass failed: Sherpa inherited OEM floor-scrub defaults and missed `drone_task`. After the fix, both SKUs are cleaning drones with drone work, not scrubbers.

| Product | Class | Capabilities |
|---------|-------|--------------|
| Sherpa Drone | cleaning_drone | avionics_task, drone_task, mobile |
| Sherpa Drone NDAA | cleaning_drone | avionics_task, drone_task, mobile |

### Tennant — PASS (empty, honest)

https://www.tennantco.com/en_us.html · range empty · 0 products

The listing did not give named robotic SKUs. FIND leaves the class picker empty. We did not invent T7AMR or a row called AMR scrubbers. Empty here is the correct answer.

### ECOVACS Commercial — PASS

https://www.ecovacscommercial.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| DEEBOT PRO M1 | cleaning | hard_floor_scrub, mobile, surface_clean |
| DEEBOT PRO K1 VAC | cleaning | hard_floor_scrub, mobile, surface_clean |

### SEER Robotics — PASS (empty, honest; was BREAK)

https://seer-robotics.ai/ · range empty · 0 products

First pass invented `Seer Humanoid` (company + morphology dump, class humanoid on a cleaning/AMR hub). That is gone. Empty is honest until a named cleaner SKU exists on the page.

### Avidbots — PASS

https://avidbots.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| Neo | cleaning | hard_floor_scrub, mobile, surface_clean |
| Neo 2W | cleaning | hard_floor_scrub, mobile, surface_clean |
| Kas | cleaning | hard_floor_scrub, mobile, surface_clean |

### Gausium — PASS (was BREAK)

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
| CD-01 | unclassified | — |
| CD-04 | unclassified | — |
| WS-01 | unclassified | — |
| WS-02 | unclassified | — |
| WS-03 | unclassified | — |

### PolarX Robotics — PASS

https://www.polarxrobotics.com/ · range cleaning

| Product | Class | Capabilities |
|---------|-------|--------------|
| Star50 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Star60 | cleaning | hard_floor_scrub, mobile, surface_clean |
| Star40 | cleaning | hard_floor_scrub, mobile, surface_clean |

### UBTECH — PASS

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
| Cruzr | unclassified | — |
| Walker | humanoid | manipulate, mobile |
| Alpha 1E | humanoid | manipulate, mobile |

### AgiBot — PASS

https://www.agibot.com/ · range humanoid

| Product | Class | Capabilities |
|---------|-------|--------------|
| A3 Ultra | humanoid | manipulate, mobile |
| Agibot A2 | humanoid | manipulate, mobile |
| Agibot G5 | humanoid | manipulate, mobile |
| G2 humanoid robot | humanoid | manipulate, mobile |
| X2 | humanoid | manipulate, mobile |
| AGIBOT G1 | humanoid | manipulate, mobile |

### MagicLab — PASS

https://www.magiclab.top/ · range humanoid, quadruped

| Product | Class | Capabilities |
|---------|-------|--------------|
| MagicLab MagicBot Gen1 | humanoid | manipulate, mobile |
| MagicBot X1 | humanoid | manipulate, mobile |
| MagicDog | quadruped | inspect_route, mobile |

### Deep Robotics — PASS

https://www.deeprobotics.cn/ · range humanoid, quadruped

| Product | Class | Capabilities |
|---------|-------|--------------|
| Deep Robotics DR02 | humanoid | manipulate, mobile |
| Deep Robotics DR01 | humanoid | manipulate, mobile |
| X20 | quadruped | inspect_route, mobile |
| X30 | quadruped | inspect_route, mobile |

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
| Fixtures | 6/6 PASS, exit 0 |
| Catalog corpus | **19/19 PASS**, 0 breaks (re-run 2026-08-31 after sibling-class fix) |
| Live sample (Lucidbots, Pudu, Tennant, SEER, Gausium) | critic ok after junk overlay. Fly still *returns* `AMR scrubbers` / `Seer Humanoid` / generic `Scrubber` until deploy |
| pstack `url_workflow` | green locally |

## Remaining gaps

1. **Fly production listing is stale.** Production still serves the old junk SKUs. The critic notes them and does not fail. Deploy this branch (or the catalog slice in #197) before treating Fly as the source of truth.
2. **Tennant and SEER stay empty.** That is honest. Do not invent T7AMR or Seer Humanoid to fill the picker.
3. **Thin SKUs.** Named but unclassified, no capabilities: Keenon Peanut / M2 / S300 / S100; Pudu FlashBot / PUDUA1 / PUDUD1 / PUDUSH1; Bear Carti; Richtech MATRADEE family, LUCKI, MEDBOT, AIDY, Scorpion, Titan; Gausium CD/WS series; UBTECH Cruzr. They do not fail the critic. They also do not help matching.
4. **Kärcher hub is KIRA only.** Correct for robotic cleaning. The rest of the Kärcher catalog is not robots.
5. Do not merge #195.

## How to re-run

`python3 scripts/url_workflow_critic.py --fixtures && python3 scripts/url_workflow_critic.py`
