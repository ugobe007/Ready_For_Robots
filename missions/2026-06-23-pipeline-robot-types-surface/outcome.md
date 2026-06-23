# Outcome: Pipeline robot types surface

**Date:** 2026-06-23  
**Status:** done

## Summary

Added `humanize_robot_types()` to slim pipeline cards (`_fmt_pipeline_card`). Harness telemetry and hero ticker now surface robot categories on every feed row.

## Verify

Pipeline cache: **35/35** leads with `robot_types_needed` (sample: Accor Hotels → cleaning/humanoid/service robots).

## Report

Cache rebuild via `scripts/refresh_pipeline_cache.py`.
