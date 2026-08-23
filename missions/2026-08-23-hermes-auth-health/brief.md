# Hermes health — auth + empty overlays

**Date:** 2026-08-23  
**Type:** build  
**Agents:** PipelineHealth

## Goal

Hermes (Mac Nous agent) is not reaching Fly. Diagnose from production, then make ingest 403s explain a `fly secrets list` fingerprint vs the real `ADMIN_KEY`, and print that body from the Cal daily digest Action.

## Acceptance

1. Public pipeline overlay counts are documented (currently empty).
2. 16-character hex `X-Admin-Key` on ingest returns 401 with “fingerprint”.
3. GHA digest workflow prints Fly’s error body on non-200.
4. `python3 scripts/hermes_health_probe.py` reports overlay coverage without secrets.

## Out of scope

Rotating GitHub/Fly secrets from this VM. Matcher / Jobs UI. Starting the Mac gateway (operator).
