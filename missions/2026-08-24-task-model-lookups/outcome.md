# Outcome — Task-model lookups, qualify filters, price maps

**Date:** 2026-08-24  
**Mission:** `missions/2026-08-24-task-model-lookups`  
**Type:** build

## Diff

- Ontology catalogs: `shared_lookups` (HF robotics / OpenVLA / LeRobot, Argo-Robot survey, Papers with Code, GitHub), `qualify_filters` (VLA vs chat LLM, license, compute, context, site), `pricing_lookups` (BenchLM, Axe physical-AI compute, Vertex/Bedrock/Azure/Databricks, OEM quote, integrator SOW).
- Resolver attaches those to every required task-model payload. Chat LLMs are a counterexample, not a warehouse/hospital policy.
- Job Card: search families, **How we qualify a candidate**, **Where to find price**. No invented dollars. Presence still unknown.

## Tests

- pytest `tests/test_robot_task_models.py` + ontology — 15 passed
- vitest Job Card + workflow — 32 passed

## Follow-ups

Named presence on a candidate. Do not scrape BenchLM into fake OEM pack prices.
