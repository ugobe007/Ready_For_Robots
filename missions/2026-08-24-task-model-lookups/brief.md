# Point task-model lookups at real FM directories, qualify filters, and price maps

**Date:** 2026-08-24  
**Type:** build  
**Agents:** ProductSurface

## Goal

Fill the three holes after PR #116: where we look for task models, how we qualify a candidate, and where price lives. Use robotics FM directories and VLA families. Do not treat chat LLMs as warehouse or hospital policies. Do not invent dollar figures.

## Acceptance

1. Shared lookups include Hugging Face robotics / OpenVLA / LeRobot, Argo-Robot manipulation survey, Papers with Code, GitHub foundation-models, Robotic Data (training data), World Labs R2S2R (sim-to-real), Mercor (talent who builds the policy — not SIGNAL).
1a. Homepage `/`: headline **Find jobs for your robot.** at display size (`text-5xl`+). Subhead **We match your robots to specific jobs and models using your URL**.
2. Qualify filters: task family (VLA vs chat LLM), commercial license, compute footprint, context, site qualification.
3. Pricing lookups: BenchLM, Axe physical-AI compute, Vertex / Bedrock / Azure / Databricks FM APIs, OEM quote, integrator SOW.
4. Job Card shows those three lists. Copy never says certificate. Presence stays unknown.

## Out of scope

Model marketplace. Scraped token prices as if they were OEM pack prices. SIGNAL / Cal.
