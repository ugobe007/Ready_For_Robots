# Mission: Pipeline cache refresh health

**Date:** 2026-06-23
**Agent:** PipelineHealth
**Status:** done
**Type:** ops

## Goal

Rebuild pipeline/homepage caches after lead-quality sweeps; confirm feed is non-empty and `cache_pending` is idle.

## Acceptance criteria

- [x] `scripts/refresh_pipeline_cache.py` full rebuild against prod DB
- [x] Live API: fresh `built_at`, no `cache_pending`, leads > 0
- [x] Harness snapshot pipeline_surface tier telemetry fixed (`priority_tier`)
- [x] Commit, push, notify
