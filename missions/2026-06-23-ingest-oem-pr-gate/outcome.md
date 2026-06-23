# Outcome: Ingest-time OEM PR gate

**Date:** 2026-06-23  
**Status:** done

## Summary

Extended `_gate_lead_vs_junk` to run `_buyer_opportunity_gate` on article context before ontology inference. Vendor funding / seller PR headlines now reject at ingest with reason `seller/vendor or publisher story`.

## Test

`test_rejects_oem_funding_pr_article` — Figure AI funding round + generic buyer name → rejected.

## Harness (post-deploy snapshot)

Recent junk sample **11%** (was ~5.8% on smaller vendor-only slice); still **100% vendor/OEM** reasons — ingest gate reduces *new* leaks; backlog quarantine still needed.
