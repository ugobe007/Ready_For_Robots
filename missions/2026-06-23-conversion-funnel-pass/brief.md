# Mission: Conversion funnel pass (browse → signup)

**Date:** 2026-06-23
**Agent:** ProductSurface
**Status:** done
**Type:** build

## Goal

Reduce friction from casual browsing to signup by fixing dead-end CTAs, post-auth landing, and upgrade moments.

## Acceptance criteria

- [x] Pricing tier CTAs route to `/signup?next=/pipeline` (honest free-workspace copy)
- [x] Signup + Login default post-auth destination `/pipeline`
- [x] Login page links to signup with preserved `?next=`
- [x] Home bottom dual CTA: Activate SIGNAL + Start free workspace
- [x] PipelinePreview “Save to workspace” → signup
- [x] Pipeline save-limit toast includes Upgrade action → `/pricing`
- [x] `docs/conversion_agent_challenges.md` published for standing agent directive
