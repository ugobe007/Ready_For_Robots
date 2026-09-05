# Pass operational job titles through to Robot Job persist

**Date:** 2026-08-25  
**Type:** build  
**Status:** in progress

## Goal

First Fly job-board cycle crawled Indeed (16 cards/page, 116 unique titles) but persisted **0** `robot_jobs`. Relevancy used ontology pain keywords only and scored line cook / housekeeper / picker below 0.15, so extract never ran. Also parse SimplyHired cards (0 postings last cycle). Remaining holes after that: exact-phrase titles ("Cook" vs "Line Cook"), a second `pain_score` gate that dropped Palletizer after relevancy passed, no JSON-LD fallback, and buyer URLs crowding the 18-URL cap.

Do not change Jobs UI, matcher ranking, or the intelligence news loop.

## Acceptance

- Line cook, housekeeper, warehouse picker, patient transporter score ≥ 0.15
- Cook, Server, Warehouse Worker, EVS Technician score ≥ 0.15
- Palletizer Operator persists (does not die on a second pain gate)
- JSON-LD JobPosting without CSS cards persists `robot_job`
- Robotics engineer still scores 0
- Indeed `job_seen_beacon` line cook HTML persists `signal_type=robot_job`
- SimplyHired `.SerpJob-jobCard` housekeeper HTML persists `robot_job`
- Rejected company name still upserts a Robot Job and does not abort the page
