# Nine OEM FIND report

**Date:** 2026-08-31
**Branch:** `cursor/more-humanoid-amr-oems-009b`
**Verdict:** critic corpus **29/29 PASS**, 0 breaks. Fixtures **8/8 PASS**.

This is the report. You do not need a terminal to read it.

Rule held: company → product → configuration → hardware → capabilities. Never company → category.

## Named products

### Booster Robotics. PASS

https://booster.tech · range humanoid · 3 products

| Product | Class | Evidence |
|---------|-------|----------|
| Booster K1 | humanoid | https://www.booster.tech/booster-k1. Homepage Humanoid Robots. KidSize platform. |
| Booster T1 | humanoid | https://www.booster.tech/booster-t1. AdultSize champion model. |
| Booster T2 | humanoid | https://www.booster.tech/booster-t2. “Redefining how humanoid robots move.” |

### Lumos Robotics. PASS

https://lumosbot.tech · range humanoid · 4 products

| Product | Class | Evidence |
|---------|-------|----------|
| Lumos LUS 2 | humanoid | https://www.lumosbot.tech/products/lus2. Full-size bipedal humanoid. |
| Lumos NIX S3 | humanoid | https://www.lumosbot.tech/products/luxiaoming. AI mini bipedal humanoid. |
| Lumos MOS 2 | unclassified | https://www.lumosbot.tech/products/mos. Heavy-duty wheeled mobile manipulation robot. |
| Lumos LUD | unclassified | https://www.lumosbot.tech/products/lud. Wheeled-legged robot. |

Not SKUs: Lumos Touch R1, FastUMI, Ego, Motor.

### Galbot. PASS

https://galbot.com · range empty (both unclassified) · 2 products

| Product | Class | Evidence |
|---------|-------|----------|
| Galbot G1 | unclassified | Site JS: “Galbot G1” / “General-purpose robot” / “embodied AI robot.” |
| Galbot S1 | unclassified | Site JS: “Galbot S1” / “Heavy-duty robot.” |

Forbidden: Galbot G2 (not on the site).

### UniX AI. PASS

https://unix-group.ai · range humanoid · 3 products

| Product | Class | Evidence |
|---------|-------|----------|
| Wanda 2.0 | humanoid | https://www.unix-group.ai/Wanda. Wheeled dual-arm humanoid. |
| Panther | humanoid | https://www.unix-group.ai/Panther. Next-gen full-size wheeled dual-arm humanoid. |
| Martian | humanoid | https://www.unix-group.ai/Martian. Bipedal humanoid. |

Forbidden: Wheeled (nav group).

### Noetix Robotics. PASS

https://noetixrobotics.com/en · range humanoid · 3 products

| Product | Class | Evidence |
|---------|-------|----------|
| Bumi | humanoid | Product menu: Bipedal Humanoid Robot Bumi. |
| N2 | humanoid | Product menu: Bipedal Humanoid Robot N2. |
| E1 | humanoid | Product menu: Bipedal Humanoid Robot E1. |

### PrimeBOT. PASS

https://primebot.cn · range humanoid · 1 product

| Product | Class | Evidence |
|---------|-------|----------|
| Q1 | humanoid | Product JS: 启元 / Q1. “全球最小全身力控人形机器人.” |

Forbidden: Qiyuan T1.

### LimX Dynamics. PASS

https://limxdynamics.com/en · range humanoid · 4 products

| Product | Class | Evidence |
|---------|-------|----------|
| Luna | humanoid | https://www.limxdynamics.com/en/products/luna. Full-size interactive humanoid. |
| Oli | humanoid | https://www.limxdynamics.com/en/products/oli. Full-size general-purpose humanoid. |
| TRON 1 | humanoid | https://www.limxdynamics.com/en/products/tron1. Multi-modal biped. Gateway to humanoid RL research. |
| TRON 2 | unclassified | https://www.limxdynamics.com/en/products/tron2. Multi-form embodied robot. Dual arms, wheeled legs. |

### Third Wave Automation. PASS (empty)

https://thirdwave.ai · no named SKU. TWA Reach removed from jobs seed.

### Dexory. PASS (empty)

https://dexory.com · no named SKU. DexoryView / Powered by AI / Impact are chrome.

## Critic

```
source=catalog ok=True urls=29 breaks=0
[PASS] https://booster.tech
[PASS] https://lumosbot.tech
[PASS] https://galbot.com
[PASS] https://unix-group.ai
[PASS] https://noetixrobotics.com/en
[PASS] https://primebot.cn
[PASS] https://limxdynamics.com/en
[PASS] https://thirdwave.ai
[PASS] https://dexory.com
```

Fixtures 8/8 PASS. VinMotion still 2. Empty Third Wave / Dexory is allowed because the page names no SKU.

## Files

- `ontology/mixed_oem_sku_catalog.v1.json`
- `app/data/vendor_robots_oem_sku_seed.json`
- `app/data/vendor_robots_jobs_seed.json` (drop TWA Reach)
- `readyforrobots-new/client/src/lib/knownOemLineups.json`
- `app/data/url_workflow_corpus.json`
- `app/services/oem_sku_discover.py`
- `app/services/vendor_robot_lookup.py` (oem_sku replaces index on these seven hosts)

Do not merge #195 or leftover #197.
