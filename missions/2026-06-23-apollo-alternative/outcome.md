# Mission: Apollo alternative + Hunter.io

**Date:** 2026-06-23  
**Status:** Done

## Problem

Apollo renewal **$588/yr** — declined. Contact gaps on HOT/WARM leads still need verified outreach emails.

## Decision

| Provider | Status | Cost |
|----------|--------|------|
| Apollo | Opt-in only (`CONTACT_USE_APOLLO=true`) | ~$588/yr — skip |
| **Hunter.io** | **Default when `HUNTER_API_KEY` set** | Free tier / ~$49/mo paid |
| Free stack | Fallback | $0 |

### Waterfall

1. CRM contact
2. Apollo (opt-in)
3. **Hunter Email Finder** (named decision makers)
4. **Hunter Domain Search** (operations/management/executive)
5. Signal text email
6. Person pattern guess
7. Website mailto
8. Role inbox

## Clay.com

Free workspace: [Clay workspace](https://app.clay.com/workspaces/1240854/chats/cc_0th3ba5YhA69u9mJ6vK) — manual enrichment / future API export; not wired in this mission.

## Ops

Set secrets:

```bash
fly secrets set HUNTER_API_KEY=your_key -a ready-2-robot
```

Contact backfill:

```bash
python3 scripts/run_lead_secondary_pass.py \
  --require-gap contact --no-apollo \
  --priority-tier HOT --priority-tier WARM \
  --limit 30 --cooldown-hours 0
```

## Files

- `app/services/hunter_client.py`
- `app/services/contact_free_sources.py`
- `app/services/lead_enrichment.py`
- `tests/test_hunter_client.py`, `tests/test_hunter_enrichment.py`
