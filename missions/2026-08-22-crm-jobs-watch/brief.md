# CRM: Jobs watch opt-in

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface + PipelineHealth

## Goal

Make `/crm` a place people come back to. Same Jobs face and emerald type. Tell them how to use CRM. Let them opt in to email when saved jobs change or new work appears for their robot. Feed that company URL into the watch cron. Free users get a real taste (1 robot, 2 emails, live events in CRM). Pro keeps watching.

## Acceptance

1. CRM headline is emerald and sits next to the Kare face.
2. Numbered how-to: pick an account → approve → send; opt in to watch the robot.
3. Opt-in checkbox emails job changes / new opportunities. Free: 1 robot, 2 alerts, events still show in CRM. Paid: unlimited watches.
4. Opt-in records the robot URL on `robot_submissions` and `jobs_watches`. Celery beat runs `run_jobs_watch_task`.
5. Pytest + Vitest green.

## Out of scope

HubSpot sync, matcher (M2) changes, SIGNAL marketing restyle.
