# Name the task models each Robot Job requires

**Date:** 2026-08-24  
**Type:** build  
**Agents:** ProductSurface + Ontology

## Goal

For each Robot Job, name the **task models** (internal nickname: certificates) the work requires and where a practitioner would look for them. Hardware in the room is not enough. Presence stays `unknown` until evidence names a model on the candidate. Do not print “certificate” in UI.

## Acceptance

1. Ontology slot JSON + resolver maps warehouse / hospital / CNC / scrub / inspect jobs to required task-model slots with lookup destinations (OEM store, Isaac, Hugging Face robotics) — not fake “this robot has GR00T.”
2. Job match API includes `required_task_models` with `presence: unknown`. Unknown models keep qualification **conditional**.
3. Expanded Job Card shows a **Task models** section (label, physical task, presence, where to look). Copy never says certificate.
4. Tests cover warehouse vs hospital slots, unknown presence, and UI copy.

## Out of scope

Model marketplace. SIGNAL / Cal. Inventing that a candidate already carries a named policy.
