# Nine OEM review

**Date:** 2026-08-31
**Branch:** `cursor/more-humanoid-amr-oems-009b`
**Score:** corpus 29/29 PASS. Fixtures 8/8 PASS.

This is the review. `report.md` in this folder has the product table.

I fetched the live pages. SPA shells (Galbot, Noetix, PrimeBOT) only name products in their JS bundles. I used those strings. I did not add a SKU that is not on the page.

## What the sites actually name

| OEM | URL | Named products | Class notes |
|-----|-----|----------------|-------------|
| Booster | https://booster.tech | K1, T1, T2 | All three sit under Humanoid Robots. T2 was missing from the old index. |
| Lumos | https://www.lumosbot.tech | LUS 2, NIX S3, MOS 2, LUD | LUS 2 and NIX S3 are bipedal humanoids. MOS 2 is a wheeled manipulator. LUD is wheeled-legged. Touch R1 / FastUMI / Motor stay out — those are a desktop arm and data tools. `lumosbot.tech` has a bad TLS cert; FIND matches the host from catalog without fetching. |
| Galbot | https://www.galbot.com | G1, S1 | JS names G1 (general-purpose robot) and S1 (heavy-duty robot). G2 is not on the site. I dropped the index G2. Neither product page calls itself a humanoid, so they stay unclassified. |
| UniX AI | https://unix-group.ai | Wanda 2.0, Panther, Martian | Wanda and Panther are wheeled dual-arm humanoids. Martian is bipedal. FIND used to pick `Wheeled` off the nav group. That is not a SKU. |
| Noetix | https://noetixrobotics.com/en | Bumi, N2, E1 | Product menu: bipedal humanoid for all three. News names (W0, W1, N1, Hobbs3) stay out. |
| PrimeBOT | https://www.primebot.cn | Q1 | Product JS: 启元 / Q1, “full-body force-controlled humanoid.” Index had Qiyuan T1. That name is not on the page. |
| LimX | https://limxdynamics.com/en | Luna, Oli, TRON 1, TRON 2 | Luna and Oli are full-size humanoids. TRON 1 is a multi-modal biped / humanoid RL platform. TRON 2 is a multi-form embodied robot (dual arms, wheeled legs). I did not dump humanoid onto TRON 2. |
| Third Wave | https://thirdwave.ai | none | Page talks about autonomous forklifts as a category. TWA Reach was a jobs-seed invention. Removed. Empty is honest. |
| Dexory | https://dexory.com | none | DexoryView is the software platform. Copy says “autonomous robots” / “autonomous tower robot” without a SKU. FIND was picking DexoryView / Powered by AI / Impact. Those are chrome. |

## Class

Company copy is not a class. Galbot’s “humanoid robotics era” line does not make G1 and S1 humanoids. LimX’s humanoid catalog does not make TRON 2 a humanoid. UniX nav “Wheeled Dual-arm Humanoid Robot” is a group label, not a product.

## Extract

Listing hints for Booster, Lumos, UniX, LimX product paths. SPA OEMs stay on catalog cache. `oem_sku` replaces the humanoid-index dump on those seven hosts so G2 / Qiyuan T1 / missing T2 cannot sit next to page names. UBTECH and the rest still merge.

## What stayed green

VinMotion still Motion 1 humanoid / Motion 2 unclassified. Tennant 5. SEER 7. Pudu mixed. Empty known OEM is still a break. Do not merge #195 or leftover #197.
