# Outcome — canonical VLA project pages on the Job Card

**Date:** 2026-08-24  
**Branch:** `cursor/task-model-vla-lookups-1962`  
**PR:** https://github.com/ugobe007/Ready_For_Robots/pull/128

## What shipped

QUALIFY lookups now point at the three practitioner pages:

- OpenVLA — https://openvla.github.io/
- Physical Intelligence π0.5 — https://www.pi.website/blog/pi05
- NVIDIA GR00T N1.5 — https://research.nvidia.com/labs/gear/gr00t-n1_5/

Tracking query params (`utm_source`, `curius`) are stripped from stored ontology URLs and from Job Card hrefs. Presence stays `unknown`. No catalog SKU is claimed to run these models.

Job Card ranking prefers those three pages over Hugging Face indexes, Isaac developer docs, surveys, talent, and price maps. Short names: OpenVLA, π0.5, GR00T N1.5.

## Verify

- `PYTHONPATH=/workspace pytest tests/test_robot_task_models.py tests/test_robot_ontology.py` — 15 passed
- vitest `robotJobCard.test.ts` — 4 passed
- Local FIND → Stretch CNC Job Card: three links with the canonical hrefs; task model Unknown

## Follow-ups

Do not ingest overlay SKUs. Do not treat these VLAs as site-qualified warehouse or hospital packs.
