# Agent verification + feature map

**Date:** 2026-08-25  
**Type:** build  
**Status:** in progress

## Goal

Give agents a scripted way to prove Jobs behavior on code changes and PRs (pstack `/create-verification-skill` shape), plus a feature map of chrome (nav, process bar, panels, surfaced results, workflow). After honest gates pass, auto-merge `cursor/*` PRs so the agent can run the improvement loop.

Do not invent jobs or dollars. Do not hop Jobs traffic onto SIGNAL. Hourly observe still does not merge.

## Acceptance

- `.cursor/skills/verify-readyforrobots/` with launch, doctor, drive, evidence, cleanup, helpers
- Feature map (index + FIND, Job Cards, Jobs chrome, Jobs CRM, About)
- `docs/feature_map.md` names nav / process bar / panels / results / workflow
- `scripts/agent_verify.py` doctor + drive; GitHub Action on PRs
- Auto-merge only after verify is green (not skip-green); never from hourly observe
- Prove doctor + one drive against production; evidence survives cleanup
