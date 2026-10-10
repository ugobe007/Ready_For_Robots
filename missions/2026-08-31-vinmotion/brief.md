# VinMotion OEM on FIND

**Date:** 2026-08-31
**Type:** build
**Branch:** `cursor/vinmotion-oem-009b`

## Goal

Add https://vinmotion.net/ the same way as Pudu / Keenon / Tennant / SEER: page evidence for product range, named products, capabilities. Do not invent SKUs.

## Acceptance

1. Named products come from the live page (Product menu + product URLs). Chrome is not a SKU.
2. Each SKU is classified from that product's hardware / work language. Company copy is not a class dump.
3. Catalog cache only. Live extract still wins.
4. Corpus URL has `expects_named_robots: true`. Empty is a BREAK.
5. Critic fixtures + corpus PASS, including VinMotion with n≥1 named robots. Other OEMs stay green.
6. Review markdown is the operator surface. PR body is one line pointing at the MD files.
7. No Fly deploy on this branch unless the operator asks.

## Out of scope

Merge #195. #197 leftover catalog draft. Invented SKUs.
