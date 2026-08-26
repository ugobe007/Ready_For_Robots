# Integrate pstack into the Jobs site

**Date:** 2026-08-26  
**Type:** build  
**Agents:** ProductSurface, Deploy

## Goal

pstack is the site’s agent protocol (How / Act / Critic) plus IDE routing. Put it on the Jobs path. Hermes stays retired. The matcher still picks jobs.

## Acceptance

1. User-visible Jobs chrome (`JobsPstackProtocol`) on `/` and About, compact on the CRM desk. Copy names ontology + `POST /api/robot-job-match` and How / Act / Critic. No chatbot. No invented dollars. Signup wall stays. Step 03 stays CRM.
2. Runtime modules: `readyforrobots-new/client/src/lib/pstackSite.ts` and `app/services/pstack_protocol.py`. CRM generate-plan tagged pstack Act. ScoutChat frozen.
3. Checked-in `.cursor/rules` work without home `pstack-models.mdc`. `docs/pstack_jobs.md` + AGENTS.md say site protocol + IDE routing.
4. verify-readyforrobots: FIND is `/`; critic is pstack; do not smoke `/experiment`.
5. vitest + pytest for the protocol. No Fly deploy. No Vercel AI Gateway. No Hermes ingest.

## Out of scope

Replace the matcher with an LLM. Customer “chat with pstack”. Remove the signup wall. SIGNAL hop. Merge the PR.
