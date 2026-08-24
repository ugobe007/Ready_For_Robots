# Hermes agent + workflow test

**Date:** 2026-08-23  
**Type:** test  
**Agents:** PipelineHealth + Hermes

## Goal

Exercise the Hermes → ReadyForRobots intelligence workflow end to end: unit ingest, live Fly contract, and Sunday `rfr-workflow-improve` findings. Do not start the Mac Hermes gateway from this VM.

## Acceptance

1. Hermes ingest pytest (auth, dry_run, fingerprint, JWT, OpenAPI contract) is green.
2. Live Fly: unauth ingest 403, `fly secrets list` fingerprint 401, Supabase JWT 401, reconstruct 200.
3. Public pipeline overlay counts are recorded (currently empty = Mac not reaching Fly).
4. Documented tracks 8–10 (buying window, customer video, vendor video, seed targets) exist in-repo with dry_run tests. Fly OpenAPI gap is recorded until deploy.
5. `scripts/hermes_health_probe.py` covers overlay + ingest contract + documented routes.

## Out of scope

Rotating Fly/GitHub `ADMIN_KEY`. Starting `hermes gateway` on the Mac. Jobs UI. Changing Cal send gates.
