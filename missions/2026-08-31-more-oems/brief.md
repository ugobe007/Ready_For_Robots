# Nine more OEM URLs on FIND

**Date:** 2026-08-31
**Type:** build
**Branch:** `cursor/more-humanoid-amr-oems-009b`

## Goal

Catalog https://booster.tech, https://lumosbot.tech, https://galbot.com, https://unix-group.ai, https://noetixrobotics.com/en, https://thirdwave.ai, https://dexory.com, https://primebot.cn, https://limxdynamics.com/en the same way as VinMotion: page evidence for named products and class. Do not invent SKUs.

## Acceptance

1. Named products come from the live page (or the site’s own JS bundle for SPA shells). Chrome is not a SKU.
2. Each SKU is classified from that product’s hardware / work language. Company copy is not a class dump.
3. Catalog cache only. Live extract still wins.
4. Empty known OEM with `expects_named_robots` is a critic break. If the page names no SKU, do not invent one.
5. Review markdown is the operator surface. PR body is one line pointing at the MD files.

## Out of scope

Merge #195. Leftover #197. Invented SKUs (Galbot G2, Qiyuan T1, TWA Reach).
