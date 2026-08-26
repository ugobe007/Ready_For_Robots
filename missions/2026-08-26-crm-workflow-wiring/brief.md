# Wire CRM into the Jobs workflow

**Date:** 2026-08-26  
**Type:** build  
**Agents:** ProductSurface

## Goal

CRM is step 03 of FIND → jobs → CRM. Checking a job dumps it into the CRM desk. Open CRM lands on that desk — no signup wall, no SIGNAL pipeline, no extra CRM click. Place this job (quote the rental) stays the money action *inside* CRM.

## Acceptance

1. Process bar 03 is labeled **CRM**. Job-list CTA is **Open CRM →**.
2. Checking a Keep row writes the CRM handoff snapshot immediately (header CRM shows those jobs).
3. Open CRM / process 03 goes to `/pipeline?src=jobs_activate` without forcing signup first.
4. Jobs header shows CRM for anonymous users (same desk href). Bare `/crm` and `/pipeline` stay SIGNAL.
5. CRM desk headline is CRM; Place this job remains the apply CTA.

## Out of scope

Matcher retune. Signed-in apply persistence. Cal. Invented rental dollars.
