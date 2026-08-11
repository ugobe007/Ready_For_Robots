# Agent Improvement Log

Proposals from Hermes `rfr-workflow-improve` (and manual reviews). Newest first.

## 2026-08-10 — Initial intelligence loop standup

### Findings

- Deployment evidence cron is live and ingesting (oem-core).
- New tracks (jobs, qualify, DMs, vendor news) shipped as Hermes skills + RFR ingest APIs.
- Gateway LaunchAgent exists but may not be loaded after reboot — cron depends on a running gateway process.

### Ranked proposals

1. **[H/L]** Confirm `hermes gateway start` / LaunchAgent loaded after reboot so 6–11am jobs fire. — owner: `hermes`
2. **[H/M]** After first job-orders tick, verify Pipeline shows `hermes_job_order` signals + Work Match overlays. — owner: `rfr-api` / product
3. **[M/M]** Expand OTTO / Rockwell query seeds (deployment tick often finds nothing). — owner: `hermes` watch files
4. **[M/L]** Pin all new crons to `ai-gateway` + `anthropic/claude-sonnet-4.6` (avoid spend-skip on drift). — owner: `hermes`
5. **[L/M]** Surface `hermes_qualify` overlay on pipeline lead detail (read-only badge). — owner: `frontend`
