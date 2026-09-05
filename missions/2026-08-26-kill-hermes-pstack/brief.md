# Kill Hermes; use pstack in the IDE

**Date:** 2026-08-26  
**Type:** build  
**Agents:** Orchestrator, Deploy

## Goal

Hermes is not a Jobs agent. Stop Mac cron, Fly ingest, and Cal outreach from acting like FIND. Use Cursor pstack for IDE routing only. Product loop stays robot URL → Job Cards.

## Acceptance

1. Constitution and product docs say Hermes is retired. Production is `/` Jobs, not `/experiment`. pstack is IDE-only.
2. Hermes Fly smoke does not `--apply` on a schedule. Scripts refuse unless `HERMES_RETIRED_OVERRIDE=1`.
3. Ingest endpoints return 410 unless `HERMES_INGEST_ENABLED=1`.
4. `fly.toml` has `CAL_AUTONOMY_ENABLED=0`. Do not enable `MARKET_GRAPH_RUN_RESEARCH` or `LEAD_RESEARCH_AGENT_ENABLED`.
5. Checked-in pstack rules: `.cursor/rules/pstack-jobs.mdc` and `.cursor/rules/pstack-rfr.mdc`. verify-readyforrobots says FIND is `/`.
6. Ontology and `robot_job_matcher.py` stay.

## Out of scope

Delete matcher or ontology. Put pstack on the website. Remove the signup wall. Merge the PR.
