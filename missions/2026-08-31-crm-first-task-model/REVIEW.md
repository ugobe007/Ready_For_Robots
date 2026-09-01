# CRM first, then apply. Name the model for the work.

**Date:** 2026-08-31
**Branch:** `cursor/crm-first-task-model-009b`
**Type:** build

## What was confusing

After FIND, the **Jobs for {robot}** list offered two siblings: violet **Apply to jobs** and emerald **Open CRM**. Same screen, two next steps. People did not know which one to hit.

Apply belongs on the CRM desk after they have the jobs. The list's only primary action is **Open CRM**.

## Path now

1. FIND (`/`) — paste URL, **Find jobs**.
2. Jobs for that robot — keep/uncheck rows. **Open CRM** only. No Apply sibling.
3. Signup wall if needed.
4. CRM desk (`/pipeline?src=jobs_activate`) — violet **Apply to jobs** prepares drafts. Open a job and answer the model question.

Copy on the list: Open CRM to save the list. Apply from the desk.

## Task model for the work

Hardware in the room is not enough. On each kept job the desk asks **Do you have a model for this work?**

- Name the model source (product, vendor, or known policy). Your words. We do not guess a name.
- Or **We'll train this for the job.**

Unknown until they answer. Stored on the kept job: `user_kept_jobs.work_task_model_kind` / `work_task_model_source`. API: `POST /api/jobs-crm/jobs/task-model`. Migration `jtm0a1b2c3d4`. Do not Fly-deploy this UX unless asked.

## Files

- FIND list CTA: `RobotJobsWorkspace.tsx`, `jobsWorkflow.ts`
- Desk apply stays: `JobsCrmDesk.tsx`, `JobsProcessChrome.tsx`
- Persist: `app/models/jobs_crm.py`, `app/services/jobs_crm.py`, `app/api/jobs_crm.py`

## Not in this PR

No Fly deploy. Draft only. Do not merge leftover #195 / #197.
