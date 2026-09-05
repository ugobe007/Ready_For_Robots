# Task-model contract + Cal jobs (not sales)

**Date:** 2026-08-25  
**Type:** build  
**Status:** in progress

## Goal

Robot companies and distributors do not know how to buy or train **task models**. Name the layers (foundation VLA vs task library vs site-adapted), who trains, how long, what data they owe, and how pricing actually works — including that field traces do **not** automatically cut the price.

Separately: Cal still optimizes robot **sales** (HOT buyers, intro emails). Daily digests read as failure when 0 intros go out. Retarget Cal copy and digest KPIs to **Robot Jobs**, and treat 0 buyer-sales intros as expected.

Do not invent dollar prices. Do not dump pricing indexes on the Job Card. Do not hop Jobs traffic onto SIGNAL buyers. Do not expand Cal into a new product.

## Acceptance

- Ontology has model layers, training time bands, data contract, pricing/field-feedback honesty
- Job Card shows a short “to place this job” contract (layer, who trains, time, data you provide)
- Open questions ask about the published pack and whether the OEM contract rebates field data
- Cal digest no longer treats 0 buyer intros + HOT queue as a stall
- Cal seller brief / persona talk about jobs for the robot, not “this buyer is a fit for your robot”
- Tests: `tests/test_robot_task_models.py`, Job Card vitest, Cal digest + seller brief
