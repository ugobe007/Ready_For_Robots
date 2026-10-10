# Nine OEM FIND report

**Date:** 2026-08-31
**Branch:** `cursor/more-humanoid-amr-oems-009b`
**Verdict:** critic fixtures PASS. Corpus PASS. All nine operator URLs have n≥1 named products.

This is the report. You do not need a terminal to read it.

Rule held: company → product → configuration → hardware → capabilities. Never company → category.

## Named products

### Booster Robotics. PASS

https://booster.tech · range humanoid · n=3

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Booster K1 | humanoid | mobile, manipulate | https://www.booster.tech/booster-k1. Humanoid robot. |
| Booster T1 | humanoid | mobile, manipulate | https://www.booster.tech/booster-t1. Humanoid robot. RoboCup AdultSize champion model. |
| Booster T2 | humanoid | mobile, manipulate | https://www.booster.tech/booster-t2. Humanoid robot. |

### Lumos Robotics. PASS

https://lumosbot.tech · range humanoid, mobile_manipulator · mixed · n=4

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Lumos LUS 2 | humanoid | mobile, manipulate | https://www.lumosbot.tech/products/lus2. Full-size bipedal humanoid. |
| Lumos NIX S3 | humanoid | mobile, manipulate | https://www.lumosbot.tech/products/luxiaoming. AI mini bipedal humanoid. |
| Lumos MOS 2 | mobile_manipulator | mobile, manipulate | https://www.lumosbot.tech/products/mos. "Heavy-Duty Wheeled Mobile Manipulation Robot." |
| Lumos LUD | unclassified | none | https://www.lumosbot.tech/products/lud. Thin English wheeled-legged page. |

Not SKUs: Lumos Touch R1, FastUMI, Ego, Motor.

### Galbot. PASS

https://galbot.com · range mobile_manipulator · n=2

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Galbot G1 | mobile_manipulator | mobile, manipulate | JS + `/g1`: "mobile dual-arm robot with generalizable manipulation." |
| Galbot S1 | mobile_manipulator | mobile, manipulate | JS + `/s1`: "Heavy-Duty Robot", 50kg payload, dual-arm handling. |

Forbidden: Galbot G2 (not a product route).

### UniX AI. PASS

https://unix-group.ai · range humanoid · n=3

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Wanda 2.0 | humanoid | mobile, manipulate | https://www.unix-group.ai/Wanda. Wheeled dual-arm humanoid. |
| Panther | humanoid | mobile, manipulate | https://www.unix-group.ai/Panther. Full-size wheeled dual-arm humanoid. |
| Martian | humanoid | mobile, manipulate | https://www.unix-group.ai/Martian. Bipedal humanoid. |

Forbidden: Wheeled (nav group).

### Noetix Robotics. PASS

https://noetixrobotics.com/en · range humanoid · n=3

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Bumi | humanoid | mobile, manipulate | `/en/detail/Bumi`. Bipedal humanoid. |
| N2 | humanoid | mobile, manipulate | `/en/detail/N2`. Bipedal humanoid. |
| E1 | humanoid | mobile, manipulate | `/en/detail/E1`. Bipedal humanoid. |

### PrimeBOT. PASS

https://primebot.cn · range humanoid · n=1

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Q1 | humanoid | mobile, manipulate | `/product/en` JS: PrimeBOT Q1, full-body force-controlled humanoid. |

Forbidden: Qiyuan T1.

### LimX Dynamics. PASS

https://limxdynamics.com/en · range humanoid, mobile_manipulator · mixed · n=4

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Luna | humanoid | mobile, manipulate | https://www.limxdynamics.com/en/products/luna. Full-size interactive humanoid. |
| Oli | humanoid | mobile, manipulate | https://www.limxdynamics.com/en/products/oli. Full-size general-purpose humanoid. |
| TRON 1 | humanoid | mobile, manipulate | https://www.limxdynamics.com/en/products/tron1. Multi-modal biped. Gateway to humanoid RL research. |
| TRON 2 | mobile_manipulator | mobile, manipulate | https://www.limxdynamics.com/en/products/tron2. "TRON 2 Autonomous Mobile Manipulation Kit." Dual arms, wheeled legs. |

### Third Wave Automation. PASS

https://thirdwave.ai · range amr · n=1

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Third Wave Reach Trucks | amr | mobile, transport | https://thirdwave.ai/armada-case-study/. "4 Third Wave Reach Trucks" / "Four Third Wave Reach trucks deployed." Autonomous forklift / reach truck. |

Forbidden: TWA Reach (invented). Homepage "autonomous forklifts" is a category, not a SKU.

### Dexory. PASS

https://dexory.com · range empty (unclassified named product) · n=1

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| DexoryView | unclassified | none | https://www.dexory.com/solutions. Named warehouse intelligence product. Page robots stay unnamed. |

Forbidden: Powered by AI, Why Dexory. No invented Dexory AMR name.

## Thin / unclassified

Lumos LUD. DexoryView (named, not a robot class). Galbot G2 / Qiyuan T1 / TWA Reach not on the page.

## Critic

```
[PASS] https://booster.tech n=3 range=['humanoid']
[PASS] https://lumosbot.tech n=4 range=['humanoid', 'mobile_manipulator']
[PASS] https://galbot.com n=2 range=['mobile_manipulator']
[PASS] https://unix-group.ai n=3 range=['humanoid']
[PASS] https://noetixrobotics.com/en n=3 range=['humanoid']
[PASS] https://primebot.cn n=1 range=['humanoid']
[PASS] https://limxdynamics.com/en n=4 range=['humanoid', 'mobile_manipulator']
[PASS] https://thirdwave.ai n=1 range=['amr']
[PASS] https://dexory.com n=1 range=[] DexoryView=None
```

`expects_named_robots: true` on all nine. Empty would BREAK.

VinMotion still 2. Tennant 5. SEER 7. Pudu mixed.

## Files

- `ontology/mixed_oem_sku_catalog.v1.json` (cache)
- `app/data/vendor_robots_oem_sku_seed.json`
- `app/data/vendor_robots_jobs_seed.json` (drop TWA Reach)
- `readyforrobots-new/client/src/lib/knownOemLineups.json`
- `app/data/url_workflow_corpus.json`
- `app/services/oem_sku_discover.py` (listing hints + known SKU words)
- `app/services/vendor_robot_lookup.py` (oem_sku replaces index on these hosts)

## Not deployed

No Fly on this branch. Catalog path is local. Do not merge #195 or leftover #197.
