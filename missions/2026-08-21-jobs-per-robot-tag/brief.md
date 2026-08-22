# Jobs: tag every job with its robot

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface

## Goal

Clean the Jobs money-maker: every job is tagged with the robot it is for. One SKU shows five jobs before signup. Several robots show one sample job per SKU so the user runs each robot individually and saves that list.

## Rule

| Lookup | Jobs on `/` | Tag |
|--------|-------------|-----|
| 1 robot | 5 example jobs | `Job 00001 is for {SKU}` |
| Several / all | 1 job per robot | `Job 00002 is for {SKU}` |

Ideal loop (copy, not a new product): run one robot → five jobs → Next → save the list to CRM. Repeat per SKU. CRM watch/email is the next retention loop — not this mission.

## Acceptance

1. Single-robot list: five jobs, each labeled `Job ##### is for {product}`.
2. Multi-robot list: one distinct sample job per robot, each labeled with that SKU.
3. Multi-robot copy tells the user to run each robot by itself for five jobs.
4. Pipeline jobs list keeps the robot tag and prompts save to CRM.
5. Vitest green.

## Out of scope

Email-on-job-change, watch subscriptions, HubSpot sync, new CRM schema.
