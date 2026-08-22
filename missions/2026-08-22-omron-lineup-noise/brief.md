# Filter OEM hub noise; cap product searches; navy CRM

**Date:** 2026-08-22  
**Type:** build  
**Agents:** LeadQuality, ProductSurface

## Goal

Professional OEM hubs (Omron mobile-robots) must not hang FIND or fill the picker with nav chrome. Search at most 3 robots (5 if paid). Activate is a save confirmation, not a repeat of step 2. CRM chrome is navy in JSX, not a CSS remap.

## Acceptance

1. Nav/locale/discontinued/overview labels never appear as robots.
2. Free/anonymous search cap is 3 products; paid is 5.
3. Research stages are honest; profile lookup aborts instead of spinning for minutes.
4. Step 3 is Save-to-CRM confirmation, not another job-card list.
5. CRM table, outreach, and account cards are navy (`bg-[#0b162f]`), not `bg-white`.
6. Targeted pytest + vitest green.

## Out of scope

Lineup segmentation for 20+ SKU catalogs (ideas only). Matcher (M2). SIGNAL expansion.
