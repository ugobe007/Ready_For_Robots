# More AMR OEM FIND report

**Date:** 2026-09-01
**Branch:** `cursor/more-amr-oem-catalog-009b`
**Verdict:** critic fixtures PASS. Corpus PASS (35/35). All six operator URLs have n≥1 named products.

This is the report. You do not need a terminal to read it.

Rule held: company → product → configuration → hardware → capabilities. Never company → category.

## Named products

### Galaxea Dynamics. PASS

https://galaxea-dynamics.com/ · range humanoid, mobile_manipulator · mixed · n=3

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| R1 Pro | humanoid | mobile, manipulate | https://galaxea-dynamics.com/products/galaxea-r1-pro-universal-humanoid-robot. "7-DOF Dual-Arm Wheeled Humanoid Robot." |
| R1 Lite | mobile_manipulator | mobile, manipulate | https://galaxea-dynamics.com/products/6-dof-general-mobile-manipulation-platform. "6-DOF General Mobile Manipulation Platform." |
| Kengo | humanoid | mobile, manipulate | https://galaxea-dynamics.com/products/galaxea-s-proprietary-embodied-ai-bipedal-robot. "embodied AI bipedal robot." |

Not SKUs: A1 Z (desktop arm), Lite-T (teleop module), G1 Gripper, VLA All-in-One Unit.

### XPENG. PASS

https://www.xpeng.com/ · range humanoid · n=1

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| IRON | humanoid | mobile, manipulate | https://www.xpeng.com/au/explore/xpeng_ai_robot_iron. "XPENG AI Robot IRON", "Next-Generation Humanoid Robot." News: https://www.xpeng.com/news/01a03797fccda01e0de68a02a256006a. |

Forbidden: XPENG Humanoid, PX5, G6, P7, G9, G3i. Homepage is cars.

### ARA Robotics. PASS

http://ararobotics.eu/ · range cleaning · n=2

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| ARI | cleaning | mobile | https://ararobotics.eu/en/ari/. "AI-Powered Autonomous Floor Maintenance Robot." |
| Petek | unclassified | none | https://ararobotics.eu/en/petek/. "Smart Maintenance Station" for ARI. Charging and water refill. |

Not SKUs: Robots, Solutions, Technology.

### Cartken. PASS

https://www.cartken.com/ · range amr · n=3

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| Cartken Hauler | amr | mobile, transport | Homepage. "Heavy-duty outdoor AMR." Payload 300 kg. |
| Cartken Courier | amr | mobile, transport | Homepage. "Outdoor AMR perfect for lightweight and secured deliveries." |
| Cartken Mover | amr | mobile, transport | Homepage. "Autonomous outdoor pallet truck" for pick and putaway. Coming soon, but the page names the work. |

Forbidden: the old "Cartken" company dump. Hauler Temperature Control is a Hauler option.

### Mobile Industrial Robots. PASS

https://mobile-industrial-robots.com/ · range amr · n=4 named on the live page (workbook still lists MiR1000 / MiR500)

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| MiR250 | amr | mobile, transport | https://mobile-industrial-robots.com/products/robots/mir250. "a more flexible AMR", 250 kg. |
| MiR600 | amr | mobile, transport | https://mobile-industrial-robots.com/products/robots/mir600. Pallet transport up to 600 kg. |
| MiR1350 | amr | mobile, transport | https://mobile-industrial-robots.com/products/robots/mir1350. "Our most powerful AMR", 1350 kg. |
| MiR1200 Pallet Jack | amr | mobile, transport | https://mobile-industrial-robots.com/products/robots/mir1200-pallet-jack. Autonomous pallet detection and delivery. |

Not SKUs: MC250, MC600 (MiR Go partners).

### Teradyne. PASS

https://www.teradyne.com/robotics/autonomous-mobile-robots/ · range amr · n=1

| Product | Class | Capabilities | Evidence |
|---------|-------|--------------|----------|
| MiR1200 Pallet Jack | amr | mobile, transport | Teradyne AMR hub: "The latest addition to MiR's AMR fleet is the MiR1200 Pallet Jack." |

Forbidden: invented MiR250 / MiR600 / MiR1350 on this page. Not J750 / UltraFLEX.

## Thin / unclassified

Petek (named station). A1 Z / Lite-T / G1 Gripper / VLA unit. Cartken Hauler Temperature Control. MiR1000 / MiR500 not on the live homepage. Teradyne does not name the rest of the MiR line.

## Critic

```
[PASS] https://galaxea-dynamics.com/ n=3 range=['humanoid', 'mobile_manipulator']
[PASS] https://www.xpeng.com/ n=1 range=['humanoid'] IRON=humanoid
[PASS] http://ararobotics.eu/ n=2 range=['cleaning'] ARI=cleaning, Petek=None
[PASS] https://www.cartken.com/ n=3 range=['amr']
[PASS] https://mobile-industrial-robots.com/ n=6 range=['amr'] (4 page + 2 workbook leftovers)
[PASS] https://www.teradyne.com/robotics/autonomous-mobile-robots/ n=1 range=['amr']
```

`expects_named_robots: true` on all six. Empty would BREAK.

Fixtures 8/8 PASS. Other corpus OEMs unchanged (VinMotion 2, Tennant 5, SEER 7, Pudu mixed).

## Files

- `ontology/mixed_oem_sku_catalog.v1.json` (cache)
- `app/data/vendor_robots_oem_sku_seed.json`
- `readyforrobots-new/client/src/lib/knownOemLineups.json`
- `app/data/url_workflow_corpus.json`
- `app/services/oem_sku_discover.py` (listing hints + known SKU words)
- `app/services/vendor_robot_lookup.py` (xpeng.com no longer junk; oem_sku replaces index on these hosts)

## Not deployed

No Fly on this branch. Catalog path is local. Do not merge leftover #197/#202. Draft #206 is separate.
