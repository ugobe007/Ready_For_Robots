# Nine OEM review

**Date:** 2026-08-31
**Branch:** `cursor/more-humanoid-amr-oems-009b`
**Score:** critic corpus PASS. Fixtures 8/8 PASS. All nine URLs have n≥1 named products.

This is the review. `report.md` in this folder has the product table.

I fetched the live sites. Galbot, Noetix, and PrimeBOT are SPA shells. Product names come from their JS bundles and product routes, not from invented SKUs.

## What the sites actually name

**Booster.** https://www.booster.tech/ names K1, T1, and T2 under Humanoid Robots. Each has its own page (`/booster-k1`, `/booster-t1`, `/booster-t2`). All three are humanoid on those pages. Studio, Champion, App, Store, RoboCup are chrome.

**Lumos.** https://www.lumosbot.tech/ names LUS 2, NIX S3, MOS 2, and LUD. LUS 2 is a full-size bipedal humanoid. NIX S3 is a mini bipedal humanoid. MOS 2 on `/products/mos` is a heavy-duty wheeled mobile manipulation robot, so FIND class is mobile_manipulator, not a sibling humanoid. LUD English copy is thin (wheeled-legged), so it stays unclassified. Touch R1 is a desktop arm. FastUMI / Ego / Motor are data tools. Those stay out.

**Galbot.** https://www.galbot.com/ is a JS SPA (`/assets/index.DR97oH2g.js`). It names Galbot G1 and Galbot S1, with routes `/g1` and `/s1`. G1 is "the world's leading mobile dual-arm robot." S1 is a heavy-duty robot, 50kg payload, dual-arm handling. G2 is not a product route. Company chrome says "humanoid robotics era." That line does not make G1 or S1 humanoids.

**UniX AI.** https://www.unix-group.ai/ names Wanda 2.0, Panther, and Martian. Wanda and Panther are wheeled dual-arm humanoids. Martian is a bipedal humanoid. The nav group "Wheeled" is not a SKU.

**Noetix.** https://www.noetixrobotics.com/en JS product list names Bumi, N2, and E1 as bipedal humanoids (`/en/detail/Bumi`, `/en/detail/N2`, `/en/detail/E1`). News names (W0, N1, Hobbs3) stay out. Hobbs W1 has a detail route but I left it out of this batch rather than guess a class.

**PrimeBOT.** https://www.primebot.cn/product/en JS names Q1, "full-body force-controlled humanoid." Index had Qiyuan T1. That name is not on the page.

**LimX.** https://www.limxdynamics.com/en/products/luna|oli|tron1|tron2. Luna and Oli are full-size humanoids. TRON 1 is a multi-modal biped / humanoid RL platform. TRON 2 is an autonomous mobile manipulation kit with dual arms and wheeled legs. I did not dump humanoid onto TRON 2.

**Third Wave.** https://thirdwave.ai/ homepage only says "autonomous forklifts" as a category. The Armada case study names **Third Wave Reach Trucks** ("4 Third Wave Reach Trucks" / "Four Third Wave Reach trucks deployed"). That is the SKU. ArmadaFMS is software. TWA Reach was a jobs-seed invention and is gone.

**Dexory.** https://www.dexory.com/ names DexoryView (warehouse intelligence platform). Copy says "our autonomous robots" and never gives those scanners a model name. DexoryView is the named product. It stays unclassified. I did not invent a Dexory AMR SKU. "Powered by AI" and "Why Dexory" stay chrome.

## Class

Work language and hardware copy on the product, not the company. Galbot G1/S1 are mobile manipulators from dual-arm / heavy-duty handling copy. Lumos MOS 2 and LimX TRON 2 are mobile manipulators. Humanoid siblings do not leak onto them. Third Wave Reach Trucks are AMRs because the page calls them autonomous forklifts / reach trucks.

## Thin / unclassified

- Lumos LUD: thin English page, wheeled-legged, no FIND class.
- DexoryView: named platform, robots on the page stay unnamed.
- Galbot G2, Qiyuan T1, TWA Reach: not on the page.

## Extract

Listing hints include product paths (Booster `/booster-t2`, Lumos `/products/mos`, Galbot `/g1` `/s1`, UniX `/Wanda`, LimX `/en/products/tron2`, Third Wave `/armada-case-study`, Dexory `/solutions`). SPA OEMs still resolve from catalog cache. `oem_sku` replaces the humanoid-index dump on these hosts so G2 / Qiyuan T1 cannot sit next to page names.

Catalog cache is `ontology/mixed_oem_sku_catalog.v1.json`. Live extract still wins.

## What stayed green

VinMotion still Motion 1 humanoid / Motion 2 unclassified. Tennant 5. SEER 7. Pudu mixed serving / cleaning / humanoid. Empty known OEM is still a break. No Fly on this branch. Do not merge #195 or leftover #197.
