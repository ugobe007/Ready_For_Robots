# Jobs: readable type + one 1970s chrome

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

The Jobs workflow works. Users still bounce because they cannot read the robot/job names, and Pipeline/CRM still look like the old SIGNAL product. Make the money-maker loop (Jobs → Pipeline → CRM) one dark 1970s terminal, with type large enough to read, a CRM headline, and a next step on every workspace page.

## Rule

| Surface | Identity | Type |
|---------|----------|------|
| `/` Jobs cards | Robot name + job title are the identity | Display sizes, never 10px |
| `/pipeline` | Headline **Pipeline**. Jobs chrome always | Same header as `/` |
| `/crm` | Headline **CRM**. Tell them what to do next | Same header, dark navy |

Do not expand SIGNAL features. Do not restyle every marketing page. Do not build email-on-job-change.

## Acceptance

1. Job cards show the robot name and job title at display size. The `Job ##### is for {SKU}` line is secondary and still readable (≥14px).
2. Jobs process bar, rail, and eyebrows are readable (≥13–14px).
3. Pipeline always uses `ExperimentHeader` (Jobs / Pipeline / CRM). No SIGNAL sales-intelligence eyebrow on the default pipeline.
4. `/crm` uses Jobs chrome, headline **CRM**, and copy that names the next step.
5. Vitest green.

## Out of scope

Watch/email retention loop, HubSpot sync, matcher (M2), full rewrite of pipeline deal-detail internals.
