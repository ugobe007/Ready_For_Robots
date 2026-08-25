# Pass operational job titles through to Robot Job persist

**Date:** 2026-08-25  
**Type:** build  
**Status:** in progress

## Goal

First Fly job-board cycle crawled Indeed (16 cards/page, 116 unique titles) but persisted **0** `robot_jobs`. Relevancy used ontology pain keywords only and scored line cook / housekeeper / picker below 0.15, so extract never ran. Also parse SimplyHired cards (0 postings last cycle).

Do not change Jobs UI, matcher ranking, or the intelligence news loop.

## Acceptance

- Line cook, housekeeper, warehouse picker, patient transporter score ≥ 0.15
- Robotics engineer still scores 0
- Indeed `job_seen_beacon` line cook HTML persists `signal_type=robot_job`
- SimplyHired `.SerpJob-jobCard` housekeeper HTML persists `robot_job`
- Rejected company name still upserts a Robot Job and does not abort the page
