# Product integrity loop — compiler + Vercel truth

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductManager, Orchestrator

## Goal

Stop skip-green Vercel production deploys. Add a Product Integrity loop (sibling of the WORK graph) with a ProductManager agent and a compiled-memory compiler. Hourly observe; daily one act; no hourly merge.

## Acceptance

1. `docs/product_integrity_loop.md` + `ontology/rfr_product_loop.v1.json` exist.
2. `Deploy frontend to Vercel` **fails** when CLI secrets are missing (no 7s green skip).
3. `python3 -m pytest tests/test_harness_compile_memory.py` passes.
4. `harness_compile_memory.py` ranks `vercel-production-cli-secrets` when the last frontend GHA is skip-green.

## Out of scope

Auto-merge. Matcher retune. Inventing jobs. Logging into the Vercel dashboard.
