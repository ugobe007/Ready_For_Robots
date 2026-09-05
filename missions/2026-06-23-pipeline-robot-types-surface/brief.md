# Mission: Pipeline robot types surface

**Date:** 2026-06-23
**Agent:** PipelineHealth
**Status:** done
**Type:** build

## Goal

Fix harness `pipeline_surface.robot_types: []` — slim pipeline cards omitted `robot_types_needed`.

## Acceptance criteria

- [x] `_fmt_pipeline_card` includes `robot_types_needed`
- [x] Cache rebuild — 35/35 feed leads carry robot types
- [x] Test coverage
